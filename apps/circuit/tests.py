from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from apps.circuit.models import Circuit
from apps.circuit.forms import CircuitForm
from apps.user.models import UserProfile
from apps.circuit.views import is_admin, serialize_circuit, json_error
from unittest.mock import patch
import json


class CircuitModelTest(TestCase):
    def test_circuit_all_features(self):
        circuit = Circuit.objects.create(
            name='Silverstone Circuit', circuit_type='RACE', direction='CW',
            location='Silverstone', country='United Kingdom', last_used=2024,
            length_km=5.891, turns=18, grands_prix='British Grand Prix',
            seasons='1950-present', grands_prix_held=58
        )
        self.assertEqual(circuit.name, 'Silverstone Circuit')
        self.assertEqual(circuit.circuit_type, 'RACE')
        self.assertEqual(circuit.direction, 'CW')
        self.assertEqual(circuit.location, 'Silverstone')
        self.assertEqual(circuit.country, 'United Kingdom')
        self.assertEqual(circuit.last_used, 2024)
        self.assertEqual(circuit.length_km, 5.891)
        self.assertEqual(circuit.turns, 18)
        self.assertEqual(str(circuit), 'Silverstone Circuit')
        self.assertEqual(circuit.grands_prix, 'British Grand Prix')
        self.assertEqual(circuit.seasons, '1950-present')
        self.assertEqual(circuit.grands_prix_held, 58)
        self.assertFalse(circuit.is_admin_created)
        self.assertIsNone(circuit.map_image_url)
        self.assertEqual(Circuit._meta.ordering, ['name'])
        self.assertEqual(Circuit._meta.verbose_name, 'Circuit')
        self.assertEqual(Circuit._meta.verbose_name_plural, 'Circuits')
        self.assertEqual(len(Circuit.CIRCUIT_TYPES), 3)
        self.assertEqual(len(Circuit.DIRECTIONS), 2)

        circuit.turns = 20
        circuit.save()
        self.assertEqual(circuit.turns, 20)

        circuit_id = circuit.id
        circuit.delete()
        self.assertFalse(Circuit.objects.filter(id=circuit_id).exists())

        circuit2 = Circuit.objects.create(
            name='Monaco Circuit', circuit_type='STREET', direction='ACW',
            location='Monte Carlo', country='Monaco', last_used=2024,
            length_km=3.337, turns=19, grands_prix='Monaco Grand Prix',
            seasons='1950-present', grands_prix_held=70,
            map_image_url='https://example.com/monaco.jpg',
            is_admin_created=True
        )
        self.assertEqual(circuit2.map_image_url, 'https://example.com/monaco.jpg')
        self.assertTrue(circuit2.is_admin_created)
        self.assertEqual(circuit2.direction, 'ACW')


class CircuitFormTest(TestCase):
    def test_circuit_form(self):
        form = CircuitForm(data={
            'name': 'Monaco Circuit', 'circuit_type': 'STREET', 'direction': 'CW',
            'location': 'Monte Carlo', 'country': 'Monaco', 'last_used': 2024,
            'length_km': 3.337, 'turns': 19, 'grands_prix': 'Monaco Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 70
        })
        self.assertTrue(form.is_valid())

        form_with_url = CircuitForm(data={
            'name': 'Spa Circuit', 'circuit_type': 'RACE', 'direction': 'CW',
            'location': 'Spa', 'country': 'Belgium', 'last_used': 2024,
            'length_km': 7.004, 'turns': 19, 'grands_prix': 'Belgian Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 60,
            'map_image_url': 'https://example.com/spa.jpg'
        })
        self.assertTrue(form_with_url.is_valid())

        invalid_form = CircuitForm(data={})
        self.assertFalse(invalid_form.is_valid())

        partial_form = CircuitForm(data={'name': 'Test', 'location': 'Test', 'country': 'Test'})
        self.assertFalse(partial_form.is_valid())


class HelperFunctionTest(TestCase):
    def test_helper_functions(self):
        factory = RequestFactory()
        user = User.objects.create_user(username='testuser', password='testpass123')
        admin = User.objects.create_user(username='admin', password='adminpass123')
        user_no_profile = User.objects.create_user(username='noprofile', password='testpass123')
        UserProfile.objects.create(id=user, role='user')
        UserProfile.objects.create(id=admin, role='admin')

        circuit = Circuit.objects.create(
            name='Test Circuit', circuit_type='RACE', direction='CW',
            location='Test Location', country='Test Country', last_used=2024,
            length_km=5.0, turns=15, grands_prix='Test GP',
            seasons='2024', grands_prix_held=1, is_admin_created=True
        )
        circuit_with_map = Circuit.objects.create(
            name='Circuit with Map', circuit_type='RACE', direction='CW',
            location='Location', country='Country', last_used=2024,
            length_km=5.0, turns=15, grands_prix='GP',
            seasons='2024', grands_prix_held=1,
            map_image_url='https://example.com/map.jpg'
        )

        request = factory.get('/')
        request.user = AnonymousUser()
        self.assertFalse(is_admin(request))

        request.user = user
        self.assertFalse(is_admin(request))

        request.user = admin
        self.assertTrue(is_admin(request))

        request.user = user_no_profile
        self.assertFalse(is_admin(request))

        request.user = admin
        result = serialize_circuit(circuit, request)
        self.assertEqual(result['id'], circuit.pk)
        self.assertEqual(result['name'], 'Test Circuit')
        self.assertEqual(result['country'], 'Test Country')
        self.assertEqual(result['location'], 'Test Location')
        self.assertEqual(result['map_image_url'], '')
        self.assertTrue(result['is_admin_created'])
        self.assertTrue(result['is_admin'])
        self.assertIn('detail_url', result)
        self.assertIn('edit_url', result)
        self.assertIn('delete_url', result)

        request.user = user
        result2 = serialize_circuit(circuit_with_map, request)
        self.assertEqual(result2['map_image_url'], 'https://example.com/map.jpg')
        self.assertFalse(result2['is_admin'])

        response = json_error('Test error message')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'Test error message')

        response2 = json_error('Server error', status=500)
        self.assertEqual(response2.status_code, 500)
        data2 = json.loads(response2.content)
        self.assertFalse(data2['ok'])
        self.assertEqual(data2['error'], 'Server error')


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
        self.admin_circuit = Circuit.objects.create(
            name='Admin Circuit', circuit_type='STREET', direction='ACW',
            location='Admin Location', country='Admin Country', last_used=2023,
            length_km=4.5, turns=16, grands_prix='Admin GP',
            seasons='2023', grands_prix_held=1, is_admin_created=True
        )

    def test_page_views(self):
        response = self.client.get(reverse('circuit:list_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit_list.html')

        response = self.client.get(reverse('circuit:detail_page', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'circuit_detail.html')
        self.assertEqual(response.context['circuit'], self.circuit)

        response = self.client.get(reverse('circuit:detail_page', args=[99999]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('circuit:add_page'))
        self.assertEqual(response.status_code, 403)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('circuit:add_page'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('circuit:edit_page', args=[self.admin_circuit.id]))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('circuit:add_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_circuit.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['page_title'], 'Add New Circuit')

        response = self.client.get(reverse('circuit:edit_page', args=[self.admin_circuit.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_circuit.html')
        self.assertIn('form', response.context)
        self.assertIn('circuit', response.context)
        self.assertEqual(response.context['page_title'], f'Edit {self.admin_circuit.name}')

        response = self.client.get(reverse('circuit:edit_page', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_detail_page_get(self):
        """GET detail page."""
        response = self.anonymous_client.get(self.detail_wiki_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['data']), 2)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('circuit:api_list'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['data']), 2)
        self.client.logout()

        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('circuit:api_list'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'Admin Circuit')
        self.client.logout()

    @patch('apps.circuit.views.Circuit.objects.all')
    def test_api_circuit_list_exception(self, mock_all):
        mock_all.side_effect = Exception('Database error')
        response = self.client.get(reverse('circuit:api_list'))
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertIn('Server error', data['error'])

    def test_api_circuit_create(self):
        data = {
            'name': 'Monaco Circuit', 'circuit_type': 'STREET', 'direction': 'CW',
            'location': 'Monte Carlo', 'country': 'Monaco', 'last_used': 2024,
            'length_km': 3.337, 'turns': 19, 'grands_prix': 'Monaco Grand Prix',
            'seasons': '1950-present', 'grands_prix_held': 70
        }

        response = self.client.post(reverse('circuit:api_create'), data)
        self.assertEqual(response.status_code, 403)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_create'), data)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('circuit:api_create'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        json_data = json.loads(response.content)
        self.assertFalse(json_data['ok'])
        self.assertEqual(json_data['error'], 'Admin role required.')
        self.client.logout()

        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Circuit.objects.filter(name='Monaco Circuit', is_admin_created=True).exists())

        response = self.client.post(reverse('circuit:api_create'), {'name': 'Incomplete', 'location': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_circuit.html')
        self.assertIn('form', response.context)
        self.client.logout()

    def test_api_circuit_update(self):
        data = {
            'name': 'Updated Circuit', 'circuit_type': 'RACE', 'direction': 'CW',
            'location': 'Updated Location', 'country': 'Updated Country', 'last_used': 2024,
            'length_km': 5.0, 'turns': 20, 'grands_prix': 'Updated GP',
            'seasons': '2024', 'grands_prix_held': 2
        }

        response = self.client.post(reverse('circuit:api_update', args=[self.admin_circuit.id]), data)
        self.assertEqual(response.status_code, 403)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_update', args=[self.admin_circuit.id]), data)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('circuit:api_update', args=[self.admin_circuit.id]), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        json_data = json.loads(response.content)
        self.assertFalse(json_data['ok'])
        self.assertEqual(json_data['error'], 'Admin role required.')
        self.client.logout()

        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_update', args=[self.admin_circuit.id]), data)
        self.assertEqual(response.status_code, 302)
        self.admin_circuit.refresh_from_db()
        self.assertEqual(self.admin_circuit.name, 'Updated Circuit')
        self.assertEqual(self.admin_circuit.turns, 20)

        response = self.client.post(reverse('circuit:api_update', args=[self.admin_circuit.id]), {'name': 'Updated', 'location': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_circuit.html')
        self.assertIn('form', response.context)
        self.assertIn('circuit', response.context)

        response = self.client.post(reverse('circuit:api_update', args=[self.circuit.id]), data)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_api_circuit_delete(self):
        response = self.client.post(reverse('circuit:api_delete', args=[self.admin_circuit.id]))
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'Admin role required.')

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('circuit:api_delete', args=[self.admin_circuit.id]))
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error'], 'Admin role required.')
        self.client.logout()

        circuit_to_delete = Circuit.objects.create(
            name='Delete Circuit', circuit_type='STREET', direction='CW',
            location='Delete Location', country='Delete Country', last_used=2024,
            length_km=3.5, turns=14, grands_prix='Delete GP',
            seasons='2024', grands_prix_held=1, is_admin_created=True
        )
        circuit_id = circuit_to_delete.id
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('circuit:api_delete', args=[circuit_id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertIn('Delete Circuit', data['message'])
        self.assertFalse(Circuit.objects.filter(id=circuit_id).exists())

        response = self.client.post(reverse('circuit:api_delete', args=[self.circuit.id]))
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertIn('Error deleting circuit', data['error'])
        self.client.logout()
