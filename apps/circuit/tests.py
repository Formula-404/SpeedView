from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.circuit.models import Circuit
from apps.circuit.forms import CircuitForm
from apps.user.models import UserProfile


class CircuitModelTest(TestCase):
    def setUp(self):
        self.circuit = Circuit.objects.create(
            name='Silverstone Circuit', circuit_type='RACE', direction='CW',
            location='Silverstone', country='United Kingdom', last_used=2024,
            length_km=5.891, turns=18, grands_prix='British Grand Prix',
            seasons='1950-present', grands_prix_held=58
        )

    def test_circuit_all_features(self):
        self.assertEqual(self.circuit.name, 'Silverstone Circuit')
        self.assertEqual(self.circuit.circuit_type, 'RACE')
        self.assertEqual(self.circuit.direction, 'CW')
        self.assertEqual(self.circuit.location, 'Silverstone')
        self.assertEqual(self.circuit.country, 'United Kingdom')
        self.assertEqual(self.circuit.last_used, 2024)
        self.assertEqual(self.circuit.length_km, 5.891)
        self.assertEqual(self.circuit.turns, 18)
        self.assertEqual(str(self.circuit), 'Silverstone Circuit')

        self.circuit.turns = 20
        self.circuit.save()
        self.assertEqual(self.circuit.turns, 20)

        circuit_id = self.circuit.id
        self.circuit.delete()
        self.assertFalse(Circuit.objects.filter(id=circuit_id).exists())


class CircuitFormTest(TestCase):
    def test_circuit_form_valid(self):
        form = CircuitForm(data={
            'name': 'Monaco Circuit', 'circuit_type': 'STREET', 'direction': 'CW',
            'location': 'Monte Carlo', 'country': 'Monaco', 'last_used': 2024,
            'length_km': 3.337, 'turns': 19, 'grands_prix': 'Monaco Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 70
        })
        self.assertTrue(form.is_valid())

    def test_circuit_form_invalid(self):
        form = CircuitForm(data={})
        self.assertFalse(form.is_valid())


class CircuitViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.admin = User.objects.create_user(username='admin', password='adminpass123')
        UserProfile.objects.create(id=self.user, role='user')
        UserProfile.objects.create(id=self.admin, role='admin')
        self.circuit = Circuit.objects.create(
            name='Silverstone Circuit', circuit_type='RACE', direction='CW',
            location='Silverstone', country='United Kingdom', last_used=2024,
            length_km=5.891, turns=18, grands_prix='British Grand Prix',
            seasons='1950-present', grands_prix_held=58
        )

    def test_circuit_list_page(self):
        response = self.client.get(reverse('circuit:list_page'))
        self.assertEqual(response.status_code, 200)

    def test_circuit_detail_page(self):
        response = self.client.get(reverse('circuit:detail_page', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 200)

    def test_add_circuit_page_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('circuit:add_page'))
        self.assertEqual(response.status_code, 403)

    def test_add_circuit_page_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('circuit:add_page'))
        self.assertEqual(response.status_code, 200)

    def test_edit_circuit_page_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('circuit:edit_page', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 403)

    def test_edit_circuit_page_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('circuit:edit_page', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 200)

    def test_api_circuit_list(self):
        response = self.client.get(reverse('circuit:api_list'))
        self.assertEqual(response.status_code, 200)

    def test_api_circuit_create_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_create'), {
            'name': 'Monaco Circuit', 'circuit_type': 'STREET', 'direction': 'CW',
            'location': 'Monte Carlo', 'country': 'Monaco', 'last_used': 2024,
            'length_km': 3.337, 'turns': 19, 'grands_prix': 'Monaco Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 70
        })
        self.assertEqual(response.status_code, 403)

    def test_api_circuit_create_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_create'), {
            'name': 'Monaco Circuit', 'circuit_type': 'STREET', 'direction': 'CW',
            'location': 'Monte Carlo', 'country': 'Monaco', 'last_used': 2024,
            'length_km': 3.337, 'turns': 19, 'grands_prix': 'Monaco Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 70
        })
        self.assertEqual(response.status_code, 302)

    def test_api_circuit_update_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_update', args=[self.circuit.id]), {
            'name': 'Silverstone Circuit Updated', 'circuit_type': 'RACE', 'direction': 'CW',
            'location': 'Silverstone', 'country': 'United Kingdom', 'last_used': 2024,
            'length_km': 5.891, 'turns': 18, 'grands_prix': 'British Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 58
        })
        self.assertEqual(response.status_code, 403)

    def test_api_circuit_update_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_update', args=[self.circuit.id]), {
            'name': 'Silverstone Circuit Updated', 'circuit_type': 'RACE', 'direction': 'CW',
            'location': 'Silverstone', 'country': 'United Kingdom', 'last_used': 2024,
            'length_km': 5.891, 'turns': 18, 'grands_prix': 'British Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 58
        })
        self.assertEqual(response.status_code, 302)

    def test_api_circuit_delete_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_delete', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 403)

    def test_api_circuit_delete_admin_access(self):
        circuit2 = Circuit.objects.create(
            name='Monaco Circuit', circuit_type='STREET', direction='CW',
            location='Monte Carlo', country='Monaco', last_used=2024,
            length_km=3.337, turns=19, grands_prix='Monaco Grand Prix',
            seasons='1950-present', grands_prix_held=70
        )
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_delete', args=[circuit2.id]))
        self.assertEqual(response.status_code, 200)
