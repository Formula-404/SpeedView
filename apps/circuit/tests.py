# Untuk menjalankan test: python manage.py test apps.circuit
# Untuk cek coverage:
# 1. pip install coverage
# 2. coverage run manage.py test apps.circuit
# 3. coverage report -m (tampilkan detail per file)
# 4. coverage html (buat laporan HTML interaktif di folder 'htmlcov')

import json
import requests # <-- IMPORT DITAMBAHKAN
from io import StringIO 
from unittest.mock import patch, MagicMock 
from django import forms # <-- IMPORT DITAMBAHKAN
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse, resolve
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect, Http404
from django.db import models 

# Import dari aplikasi circuit Anda
from .models import Circuit
from .forms import CircuitForm
from .views import ( 
    is_admin, serialize_circuit, json_error,
    circuit_list_page, circuit_detail_page, add_circuit_page, edit_circuit_page,
    api_circuit_list, api_circuit_create, api_circuit_update, api_circuit_delete
)
from .admin import CircuitAdmin
# Import command 
from .management.commands import import_circuit 

# ================== Mock User Profile (Hanya untuk Testing) ==================
class MockProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    role = models.CharField(max_length=10, default='user')

    class Meta:
        app_label = 'circuit' 
        # db_table = 'circuit_mockprofile_testing' # Biarkan Django menamai otomatis
        # managed = False <-- DIHAPUS agar tabel dibuat di test DB

# ================== Test Cases ==================

class CircuitModelTests(TestCase):
    """Menguji model Circuit."""

    def test_circuit_creation_and_defaults(self):
        """Test pembuatan objek Circuit dan nilai defaultnya."""
        circuit = Circuit.objects.create(
            name="Test Circuit", location="Test Loc", country="TC",
            length_km=5.0, turns=15, grands_prix="Test GP",
            seasons="2024", grands_prix_held=1
        )
        self.assertEqual(str(circuit), "Test Circuit")
        self.assertEqual(circuit.circuit_type, 'RACE') 
        self.assertEqual(circuit.direction, 'CW')     
        self.assertFalse(circuit.is_admin_created)    
        self.assertIsNone(circuit.map_image_url)      
        self.assertIsNone(circuit.last_used)          

    def test_verbose_names(self):
        """Test verbose names di Meta."""
        self.assertEqual(Circuit._meta.verbose_name, "Circuit")
        self.assertEqual(Circuit._meta.verbose_name_plural, "Circuits")

    def test_ordering(self):
        """Test ordering default di Meta."""
        Circuit.objects.create(name="Beta Circuit", location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        Circuit.objects.create(name="Alpha Circuit", location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        circuits = list(Circuit.objects.all())
        self.assertEqual(circuits[0].name, "Alpha Circuit")
        self.assertEqual(circuits[1].name, "Beta Circuit")

class CircuitFormTests(TestCase):
    """Menguji CircuitForm."""

    def test_valid_form_all_fields(self):
        """Test form dengan semua data valid."""
        data = {
            'name': 'Valid Circuit', 'location': 'Valid Loc', 'country': 'VC',
            'length_km': 5.5, 'turns': 12, 'grands_prix': 'Valid GP',
            'seasons': '2024-2025', 'grands_prix_held': 2, 'circuit_type': 'ROAD',
            'direction': 'ACW', 'map_image_url': 'https://example.com/map.png',
            'last_used': 2025
        }
        form = CircuitForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}")

    def test_valid_form_optional_fields_blank(self):
        """Test form valid dengan field opsional kosong."""
        data = {
            'name': 'Optional Blank', 'location': 'Loc', 'country': 'Co',
            'length_km': 5.0, 'turns': 10, 'grands_prix': 'GP',
            'seasons': '2024', 'grands_prix_held': 1, 
            'circuit_type': 'RACE', # <-- DITAMBAHKAN (meski ada default, form mungkin perlu)
            'direction': 'CW',     # <-- DITAMBAHKAN
            'map_image_url': '',   # Opsional (blank=True)
            # last_used tidak diisi (null=True)
        }
        form = CircuitForm(data=data)
        self.assertTrue(form.is_valid(), msg=f"Form errors: {form.errors.as_json()}") # Seharusnya valid sekarang

    def test_invalid_form_missing_required(self):
        """Test form dengan field wajib yang kosong."""
        required_fields = ['name', 'location', 'country', 'length_km', 'turns', 'grands_prix', 'seasons', 'grands_prix_held']
        data = {'circuit_type': 'STREET', 'direction': 'CW'} 
        form = CircuitForm(data=data)
        self.assertFalse(form.is_valid())
        for field in required_fields:
            self.assertIn(field, form.errors, msg=f"Field '{field}' seharusnya wajib.")

    def test_invalid_form_bad_data_type(self):
        """Test form dengan tipe data yang salah."""
        data = {
            'name': 'Bad Type Circuit', 'location': 'Loc', 'country': 'Co',
            'length_km': 'abc', 
            'turns': 10.5,      
            'grands_prix': 'GP', 'seasons': 'S', 'grands_prix_held': 'one', 
            'map_image_url': 'not a valid url', 
            'last_used': 'yesterday',
            'circuit_type': 'RACE', # Perlu ada untuk field lain divalidasi
            'direction': 'CW',      # Perlu ada
        }
        form = CircuitForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('length_km', form.errors)
        self.assertIn('turns', form.errors)
        self.assertIn('grands_prix_held', form.errors)
        self.assertIn('map_image_url', form.errors)
        self.assertIn('last_used', form.errors)

    def test_form_widgets_and_placeholders(self):
        """Test apakah widget dan placeholder diatur dengan benar."""
        form = CircuitForm()
        self.assertIn('input-field', form.fields['name'].widget.attrs['class'])
        self.assertEqual(form.fields['name'].widget.attrs['placeholder'], 'e.g., Silverstone Circuit')
        # Gunakan 'forms.' yang sudah diimpor
        self.assertIsInstance(form.fields['circuit_type'].widget, forms.Select) 
        self.assertIn('input-field', form.fields['circuit_type'].widget.attrs['class'])

# ... (CircuitViewHelperTests tetap sama) ...
class CircuitViewHelperTests(TestCase):
    """Menguji fungsi helper di views.py."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_user(username='helperadmin', password='password')
        cls.non_admin_user = User.objects.create_user(username='helperuser', password='password')
        MockProfile.objects.create(user=cls.admin_user, role='admin')
        MockProfile.objects.create(user=cls.non_admin_user, role='user')
        cls.circuit = Circuit.objects.create(name="Helper Circuit", location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)

    def test_is_admin_helper(self):
        """Test fungsi is_admin."""
        factory = RequestFactory()
        
        request_admin = factory.get('/')
        request_admin.user = self.admin_user
        request_admin.user.profile = MockProfile.objects.get(user=self.admin_user)
        self.assertTrue(is_admin(request_admin))

        request_user = factory.get('/')
        request_user.user = self.non_admin_user
        request_user.user.profile = MockProfile.objects.get(user=self.non_admin_user)
        self.assertFalse(is_admin(request_user))

        request_anon = factory.get('/')
        request_anon.user = AnonymousUser()
        self.assertFalse(is_admin(request_anon))
        
        user_no_profile = User.objects.create_user(username='noprofile', password='password')
        request_no_profile = factory.get('/')
        request_no_profile.user = user_no_profile
        self.assertFalse(MockProfile.objects.filter(user=user_no_profile).exists())
        self.assertFalse(is_admin(request_no_profile))

    def test_serialize_circuit_helper(self):
        """Test fungsi serialize_circuit."""
        factory = RequestFactory()
        request_admin = factory.get('/')
        request_admin.user = self.admin_user 
        request_admin.user.profile = MockProfile.objects.get(user=self.admin_user)
        
        serialized = serialize_circuit(self.circuit, request_admin)
        
        self.assertEqual(serialized['id'], self.circuit.pk)
        self.assertEqual(serialized['name'], self.circuit.name)
        self.assertTrue(serialized['is_admin']) 
        self.assertIn('detail_url', serialized)
        self.assertIn('edit_url', serialized)
        self.assertIn('delete_url', serialized)
        self.assertFalse(serialized['is_admin_created']) 
        
        circuit_blank = Circuit(pk=99, name="Blank Test") 
        serialized_blank = serialize_circuit(circuit_blank, request_admin)
        self.assertEqual(serialized_blank['country'], "")
        self.assertEqual(serialized_blank['location'], "")
        self.assertEqual(serialized_blank['map_image_url'], "")

    def test_json_error_helper(self):
        """Test fungsi json_error."""
        response = json_error("Error message", status=403)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], "Error message")

# ... (CircuitViewAccessAndLogicTests tetap sama) ...
class CircuitViewAccessAndLogicTests(TestCase):
    """Menguji akses, permission, dan logika dasar semua view."""

    @classmethod
    def setUpTestData(cls):
        # User Setup
        cls.admin_user = User.objects.create_user(username='viewadmin', password='p', is_staff=True)
        cls.non_admin_user = User.objects.create_user(username='viewuser', password='p')
        MockProfile.objects.create(user=cls.admin_user, role='admin')
        MockProfile.objects.create(user=cls.non_admin_user, role='user')

        # Circuit Setup
        cls.circuit_admin = Circuit.objects.create(name="VAdmin Circuit", is_admin_created=True, location="AdminLoc", country="AC", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        cls.circuit_wiki = Circuit.objects.create(name="VWiki Circuit", is_admin_created=False, location="WikiLoc", country="WC", length_km=2, turns=2, grands_prix="G", seasons="S", grands_prix_held=2)

        # Clients
        cls.admin_client = Client()
        cls.admin_client.login(username='viewadmin', password='p')
        cls.non_admin_client = Client()
        cls.non_admin_client.login(username='viewuser', password='p')
        cls.anonymous_client = Client()

        # URLs
        cls.list_url = reverse('circuit:list_page')
        cls.detail_admin_url = reverse('circuit:detail_page', kwargs={'pk': cls.circuit_admin.pk})
        cls.detail_wiki_url = reverse('circuit:detail_page', kwargs={'pk': cls.circuit_wiki.pk})
        cls.add_url = reverse('circuit:add_page')
        cls.edit_admin_url = reverse('circuit:edit_page', kwargs={'pk': cls.circuit_admin.pk})
        cls.edit_wiki_url = reverse('circuit:edit_page', kwargs={'pk': cls.circuit_wiki.pk}) 
        cls.api_list_url = reverse('circuit:api_list')
        cls.api_create_url = reverse('circuit:api_create')
        cls.api_update_admin_url = reverse('circuit:api_update', kwargs={'pk': cls.circuit_admin.pk})
        cls.api_update_wiki_url = reverse('circuit:api_update', kwargs={'pk': cls.circuit_wiki.pk}) 
        cls.api_delete_admin_url = reverse('circuit:api_delete', kwargs={'pk': cls.circuit_admin.pk})
        cls.api_delete_wiki_url = reverse('circuit:api_delete', kwargs={'pk': cls.circuit_wiki.pk}) 

        # Data for POST
        cls.valid_data = {'name': 'New Circuit Test', 'location': 'NewLoc', 'country': 'NC', 'length_km': 3, 'turns': 3, 'grands_prix': 'NGP', 'seasons': 'NewS', 'grands_prix_held': 3, 'circuit_type': 'RACE', 'direction': 'CW'} # Tambah field default
        cls.invalid_data = {'name': '', 'location': 'L', 'country': 'C', 'length_km': 1, 'turns': 1, 'grands_prix': 'G', 'seasons': 'S', 'grands_prix_held': 1} # Nama kosong

    # --- Test Page Views (GET Requests) ---
    def test_list_page_get(self):
        """GET list page."""
        response = self.anonymous_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit/circuit_list.html')

    def test_detail_page_get(self):
        """GET detail page."""
        response = self.anonymous_client.get(self.detail_wiki_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit/circuit_detail.html')
        self.assertEqual(response.context['circuit'], self.circuit_wiki)
        
        # Test 404
        response_404 = self.anonymous_client.get(reverse('circuit:detail_page', kwargs={'pk': 999}))
        self.assertEqual(response_404.status_code, 404)

    def test_add_page_get_permissions(self):
        """GET add page permissions."""
        response_admin = self.admin_client.get(self.add_url)
        self.assertEqual(response_admin.status_code, 200)
        self.assertTemplateUsed(response_admin, 'circuit/add_circuit.html')
        self.assertIsInstance(response_admin.context['form'], CircuitForm)
        
        self.assertEqual(self.non_admin_client.get(self.add_url).status_code, 403)
        self.assertRedirects(self.anonymous_client.get(self.add_url), '/accounts/login/?next=/circuit/add/')

    def test_edit_page_get_permissions(self):
        """GET edit page permissions."""
        response_admin_ok = self.admin_client.get(self.edit_admin_url)
        self.assertEqual(response_admin_ok.status_code, 200)
        self.assertTemplateUsed(response_admin_ok, 'circuit/edit_circuit.html')
        self.assertEqual(response_admin_ok.context['circuit'], self.circuit_admin)
        self.assertIsInstance(response_admin_ok.context['form'], CircuitForm)
        
        response_admin_fail = self.admin_client.get(self.edit_wiki_url)
        self.assertEqual(response_admin_fail.status_code, 404) 
        
        self.assertEqual(self.non_admin_client.get(self.edit_admin_url).status_code, 403)
        self.assertRedirects(self.anonymous_client.get(self.edit_admin_url), f'/accounts/login/?next={self.edit_admin_url}')
        
        response_404 = self.admin_client.get(reverse('circuit:edit_page', kwargs={'pk': 999}))
        self.assertEqual(response_404.status_code, 404)

    # --- Test API Views (GET Request) ---
    def test_api_list_get_data_permissions(self):
        """GET api list returns correct data based on role."""
        response_admin = self.admin_client.get(self.api_list_url)
        self.assertEqual(response_admin.status_code, 200)
        data_admin = response_admin.json()
        self.assertTrue(data_admin['ok'])
        self.assertEqual(len(data_admin['data']), 1) 
        self.assertEqual(data_admin['data'][0]['name'], self.circuit_admin.name)

        for client in [self.non_admin_client, self.anonymous_client]:
            response = client.get(self.api_list_url)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['ok'])
            self.assertEqual(len(data['data']), 2) 

    # --- Test API Views (POST Requests) ---
    def test_api_create_post_permissions_and_logic(self):
        """POST api create permissions and success logic."""
        initial_admin_count = Circuit.objects.filter(is_admin_created=True).count()
        response_admin = self.admin_client.post(self.api_create_url, data=self.valid_data)
        self.assertRedirects(response_admin, self.list_url)
        self.assertEqual(Circuit.objects.filter(is_admin_created=True).count(), initial_admin_count + 1)
        new_circuit = Circuit.objects.get(name=self.valid_data['name'])
        self.assertTrue(new_circuit.is_admin_created)
        
        response_user_ajax = self.non_admin_client.post(self.api_create_url, data=self.valid_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_user_ajax.status_code, 403)
        self.assertFalse(json.loads(response_user_ajax.content)['ok'])
        response_user_noajax = self.non_admin_client.post(self.api_create_url, data=self.valid_data)
        self.assertEqual(response_user_noajax.status_code, 403)
        
        response_anon = self.anonymous_client.post(self.api_create_url, data=self.valid_data)
        self.assertRedirects(response_anon, f'/accounts/login/?next={self.api_create_url}')
        
    def test_api_create_post_invalid(self):
        """POST api create with invalid data re-renders form."""
        initial_count = Circuit.objects.count()
        response = self.admin_client.post(self.api_create_url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit/add_circuit.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(Circuit.objects.count(), initial_count) # Pastikan tidak ada yg dibuat

    def test_api_update_post_permissions_and_logic(self):
        """POST api update permissions and success logic."""
        updated_name = "Updated by API Test"
        data = self.valid_data.copy()
        data['name'] = updated_name
        
        response_admin_ok = self.admin_client.post(self.api_update_admin_url, data=data)
        self.assertRedirects(response_admin_ok, self.list_url)
        self.circuit_admin.refresh_from_db()
        self.assertEqual(self.circuit_admin.name, updated_name)

        response_admin_fail = self.admin_client.post(self.api_update_wiki_url, data=data)
        self.assertEqual(response_admin_fail.status_code, 404)

        response_user_ajax = self.non_admin_client.post(self.api_update_admin_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_user_ajax.status_code, 403)
        response_user_noajax = self.non_admin_client.post(self.api_update_admin_url, data=data)
        self.assertEqual(response_user_noajax.status_code, 403)
        
        response_anon = self.anonymous_client.post(self.api_update_admin_url, data=data)
        self.assertRedirects(response_anon, f'/accounts/login/?next={self.api_update_admin_url}')

    def test_api_update_post_invalid(self):
        """POST api update with invalid data re-renders form."""
        original_name = self.circuit_admin.name
        response = self.admin_client.post(self.api_update_admin_url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit/edit_circuit.html')
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(response.context['circuit'], self.circuit_admin) 
        self.circuit_admin.refresh_from_db()
        self.assertEqual(self.circuit_admin.name, original_name) # Nama tidak berubah

    def test_api_delete_post_permissions_and_logic(self):
        """POST api delete permissions and success logic."""
        c_to_delete = Circuit.objects.create(name="ToDeleteAPI", is_admin_created=True, location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        delete_url = reverse('circuit:api_delete', kwargs={'pk': c_to_delete.pk})
        
        # Admin delete circuit admin -> Sukses (JSON response)
        response_admin_ok = self.admin_client.post(delete_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response_admin_ok.status_code, 200)
        self.assertTrue(json.loads(response_admin_ok.content)['ok'])
        self.assertFalse(Circuit.objects.filter(pk=c_to_delete.pk).exists())

        # Admin delete circuit wiki -> 404
        response_admin_fail = self.admin_client.post(self.api_delete_wiki_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response_admin_fail.status_code, 404)

        # Non-Admin -> 403 (JSON response)
        response_user = self.non_admin_client.post(self.api_delete_admin_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response_user.status_code, 403)
        self.assertFalse(json.loads(response_user.content)['ok'])
        
        # Anonymous -> 403 (JSON response)
        response_anon = self.anonymous_client.post(self.api_delete_admin_url, HTTP_ACCEPT='application/json')
        self.assertEqual(response_anon.status_code, 403)
        self.assertFalse(json.loads(response_anon.content)['ok'])

        # Test delete 404 (non-existent admin circuit)
        response_404_admin = self.admin_client.post(reverse('circuit:api_delete', kwargs={'pk': 999}), HTTP_ACCEPT='application/json')
        self.assertEqual(response_404_admin.status_code, 404) 

class CircuitURLConfTests(TestCase):
    """Menguji pemetaan URL ke view."""

    def test_url_resolutions(self):
        """Test URL paths resolve ke view function yang benar."""
        # Gunakan resolve dari django.urls
        self.assertEqual(resolve('/circuit/').func, circuit_list_page)
        self.assertEqual(resolve('/circuit/1/').func, circuit_detail_page)
        self.assertEqual(resolve('/circuit/add/').func, add_circuit_page)
        self.assertEqual(resolve('/circuit/1/edit/').func, edit_circuit_page)
        self.assertEqual(resolve('/circuit/api/').func, api_circuit_list)
        self.assertEqual(resolve('/circuit/api/create/').func, api_circuit_create)
        self.assertEqual(resolve('/circuit/api/1/update/').func, api_circuit_update)
        self.assertEqual(resolve('/circuit/api/1/delete/').func, api_circuit_delete)

    def test_url_name_reversals(self):
        """Test view names reverse ke URL path yang benar."""
        self.assertEqual(reverse('circuit:list_page'), '/circuit/')
        self.assertEqual(reverse('circuit:detail_page', kwargs={'pk': 1}), '/circuit/1/')
        self.assertEqual(reverse('circuit:add_page'), '/circuit/add/')
        self.assertEqual(reverse('circuit:edit_page', kwargs={'pk': 1}), '/circuit/1/edit/')
        self.assertEqual(reverse('circuit:api_list'), '/circuit/api/')
        self.assertEqual(reverse('circuit:api_create'), '/circuit/api/create/')
        self.assertEqual(reverse('circuit:api_update', kwargs={'pk': 1}), '/circuit/api/1/update/')
        self.assertEqual(reverse('circuit:api_delete', kwargs={'pk': 1}), '/circuit/api/1/delete/')


class CircuitAdminConfTests(TestCase):
    """Menguji konfigurasi di admin.py."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser('adminconf', 'ac@example.com', 'p')
        cls.site = AdminSite() 
        cls.model_admin = CircuitAdmin(Circuit, cls.site) 
        cls.circuit_admin = Circuit.objects.create(name="AdminConfCircuit", is_admin_created=True, location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        cls.circuit_wiki = Circuit.objects.create(name="WikiConfCircuit", is_admin_created=False, location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        # Tambahkan RequestFactory
        cls.factory = RequestFactory() 

    def test_get_queryset_filters_admin_created(self):
        """Test get_queryset hanya menampilkan is_admin_created=True."""
        request = self.factory.get('/') # Gunakan RequestFactory
        request.user = self.admin_user 
        
        queryset = self.model_admin.get_queryset(request)
        
        self.assertIn(self.circuit_admin, queryset)
        self.assertNotIn(self.circuit_wiki, queryset)
        self.assertEqual(queryset.count(), 1)

    def test_save_model_sets_flag(self):
        """Test save_model otomatis set is_admin_created=True."""
        request = self.factory.get('/') # Gunakan RequestFactory
        request.user = self.admin_user
        
        new_circuit = Circuit(name="SavedViaAdminTest", location="L", country="C", length_km=1, turns=1, grands_prix="G", seasons="S", grands_prix_held=1)
        # Mock form sederhana sudah cukup
        form = CircuitForm(instance=new_circuit) 
        
        # Panggil save_model 
        self.model_admin.save_model(request, new_circuit, form, change=False)
        
        # Cek objek yang tersimpan
        saved = Circuit.objects.get(name="SavedViaAdminTest")
        self.assertTrue(saved.is_admin_created)
        
        # Test juga untuk update (change=True)
        saved.name = "UpdatedViaAdmin"
        # Buat instance form baru untuk update
        form_update = CircuitForm(instance=saved, data={'name': 'UpdatedViaAdmin', 'location': 'L', 'country': 'C', 'length_km': 1, 'turns': 1, 'grands_prix': 'G', 'seasons': 'S', 'grands_prix_held': 1})
        self.assertTrue(form_update.is_valid()) # Pastikan form valid
        self.model_admin.save_model(request, saved, form_update, change=True)
        saved.refresh_from_db()
        self.assertTrue(saved.is_admin_created) # Flag harus tetap True

    def test_admin_list_display_and_filters(self):
        """Cek konfigurasi list_display dan list_filter."""
        self.assertIn('is_admin_created', self.model_admin.list_display)
        self.assertIn('is_admin_created', self.model_admin.list_filter)

class CircuitImportCommandTests(TestCase):
    """Menguji management command import_circuit (seed_circuits)."""

    @patch('apps.circuit.management.commands.import_circuit.requests.get')
    def test_command_success_creates_objects(self, mock_requests_get):
        """Test command berjalan sukses dan membuat objek Circuit."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.content = """
        <html><body>
            <table class="wikitable sortable">
                <thead><tr><th>Circuit</th><th>Map</th><th>Type</th><th>Direction</th><th>Location</th><th>Country</th><th>Last length used</th><th>Turns</th><th>Grands Prix</th><th>Season(s)</th><th>Grands Prix held</th></tr></thead>
                <tbody>
                    <tr><td><a href="/wiki/Test">Test Circuit</a></td><td><img src="//example.com/map.png"/></td><td>Race circuit</td><td>Clockwise</td><td>Test Loc</td><td> Test Country </td><td>5.1 km</td><td>12</td><td>Test GP</td><td>2024</td><td>1</td></tr>
                    <tr><td>No Link Circuit</td><td></td><td>Street Circuit</td><td>Anti-Clockwise</td><td>Loc2</td><td> Country 2 </td><td>3 km</td><td>8</td><td>GP2</td><td>2023</td><td>2</td></tr>
                </tbody>
            </table>
        </body></html>
        """.encode('utf-8')
        mock_requests_get.return_value = mock_response

        out = StringIO()
        call_command('import_circuit', stdout=out) 
        
        self.assertEqual(Circuit.objects.count(), 2) # Sekarang seharusnya 2
        circuit1 = Circuit.objects.get(name="Test Circuit")
        self.assertEqual(circuit1.country, "Test Country")
        self.assertEqual(circuit1.map_image_url, "https://example.com/map.png")
        self.assertFalse(circuit1.is_admin_created) 

        circuit2 = Circuit.objects.get(name="No Link Circuit")
        self.assertEqual(circuit2.country, "Country 2")
        self.assertFalse(circuit2.is_admin_created)
        
        self.assertIn("Scraping selesai", out.getvalue())
        self.assertIn("2 sirkuit ditambahkan", out.getvalue())

    @patch('apps.circuit.management.commands.import_circuit.requests.get')
    def test_command_request_exception(self, mock_requests_get):
        """Test command jika requests.get memunculkan exception."""
        mock_requests_get.side_effect = requests.exceptions.RequestException("Network Error")
        
        out = StringIO() # Tangkap stdout untuk pesan error command
        call_command('import_circuit', stdout=out, stderr=StringIO()) # Arahkan stderr juga
        self.assertEqual(Circuit.objects.count(), 0) 
        self.assertIn("Gagal mengambil halaman Wikipedia", out.getvalue()) # Error dicetak ke stdout oleh command

    @patch('apps.circuit.management.commands.import_circuit.requests.get')
    def test_command_table_not_found(self, mock_requests_get):
        """Test command jika tabel tidak ditemukan di HTML."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.content = "<html><body>No relevant table here</body></html>".encode('utf-8')
        mock_requests_get.return_value = mock_response

        out = StringIO() 
        call_command('import_circuit', stdout=out, stderr=StringIO())
        self.assertEqual(Circuit.objects.count(), 0)
        self.assertIn("Tidak dapat menemukan tabel sirkuit utama", out.getvalue()) # Error dicetak ke stdout

    @patch('apps.circuit.management.commands.import_circuit.requests.get')
    def test_command_header_mismatch(self, mock_requests_get):
        """Test command jika header tabel tidak cocok."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.content = """
        <html><body>
            <table class="wikitable sortable">
                <thead><tr><th>Circuit</th><th>WRONG HEADER</th><th>Type</th><th>Direction</th><th>Location</th><th>Country</th><th>Last length used</th><th>Turns</th><th>Grands Prix</th><th>Season(s)</th><th>Grands Prix held</th></tr></thead>
                <tbody><tr><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td><td>Data</td></tr></tbody>
            </table>
        </body></html>
        """.encode('utf-8')
        mock_requests_get.return_value = mock_response

        out = StringIO()
        call_command('import_circuit', stdout=out, stderr=StringIO())
        self.assertEqual(Circuit.objects.count(), 0)
        # Cek pesan error spesifik dari find_main_circuit_table
        self.assertIn("Tidak dapat menemukan tabel sirkuit utama dengan header yang diharapkan", out.getvalue()) 