from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.car.models import Car
from apps.car.forms import CarForm
from apps.driver.models import Driver, DriverEntry
from apps.meeting.models import Meeting
from apps.session.models import Session
from apps.user.models import UserProfile


class CarModelTest(TestCase):
    def setUp(self):
        self.driver = Driver.objects.create(driver_number=1, full_name='Test Driver')
        self.meeting = Meeting.objects.create(meeting_key=1, meeting_name='Test GP', year=2024)
        self.session = Session.objects.create(session_key=1, meeting_key=1, name='Race', start_time=timezone.now())
        self.car = Car.objects.create(
            driver_number=1, session_key=1, meeting_key=1, date=timezone.now(),
            brake=100, drs=0, n_gear=5, rpm=10000, speed=200, throttle=80, is_manual=True, driver=self.driver
        )

    def test_car_all_features(self):
        self.assertEqual(self.car.driver_number, 1)
        self.assertEqual(self.car.session_key, 1)
        self.assertEqual(self.car.meeting_key, 1)
        self.assertEqual(self.car.brake, 100)
        self.assertEqual(self.car.drs, 0)
        self.assertEqual(self.car.n_gear, 5)
        self.assertEqual(self.car.rpm, 10000)
        self.assertEqual(self.car.speed, 200)
        self.assertEqual(self.car.throttle, 80)
        self.assertEqual(self.car.is_manual, True)
        self.assertEqual(self.car.driver, self.driver)
        self.assertIn('1 |', str(self.car))
        self.assertEqual(self.car.drs_state, 'DRS off')
        self.assertEqual(self.car.meeting_key_value, 1)
        self.assertEqual(self.car.session_key_value, 1)

        self.car.speed = 250
        self.car.save()
        self.assertEqual(self.car.speed, 250)

        car_id = self.car.id
        self.car.delete()
        self.assertFalse(Car.objects.filter(id=car_id).exists())


class CarFormTest(TestCase):
    def setUp(self):
        self.meeting = Meeting.objects.create(meeting_key=1, meeting_name='Test GP', year=2024)
        self.session = Session.objects.create(session_key=1, meeting_key=1, name='Race', start_time=timezone.now())
        self.driver = Driver.objects.create(driver_number=1, full_name='Test Driver')
        self.entry = DriverEntry.objects.create(driver=self.driver, session_key=1, meeting=self.meeting)

    def test_car_form_valid(self):
        form = CarForm(data={
            'meeting_key': 1, 'session_key': 1, 'driver_number': 1, 'speed': 200,
            'throttle': 80, 'brake': 100, 'n_gear': 5, 'rpm': 10000, 'drs': 0, 'session_offset_seconds': 10
        }, meeting_choices=[(1, 'Test GP')])
        self.assertTrue(form.is_valid())

    def test_car_form_invalid_no_session(self):
        form = CarForm(data={
            'meeting_key': 1, 'driver_number': 1, 'speed': 200,
            'throttle': 80, 'brake': 100, 'n_gear': 5, 'rpm': 10000, 'drs': 0
        }, meeting_choices=[(1, 'Test GP')])
        self.assertFalse(form.is_valid())

    def test_car_form_save(self):
        form = CarForm(data={
            'meeting_key': 1, 'session_key': 1, 'driver_number': 1, 'speed': 200,
            'throttle': 80, 'brake': 100, 'n_gear': 5, 'rpm': 10000, 'drs': 0, 'session_offset_seconds': 10
        }, meeting_choices=[(1, 'Test GP')])
        self.assertTrue(form.is_valid())
        car = form.save()
        self.assertTrue(car.is_manual)


class CarViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.admin = User.objects.create_user(username='admin', password='adminpass123')
        UserProfile.objects.create(id=self.user, role='user')
        UserProfile.objects.create(id=self.admin, role='admin')
        self.meeting = Meeting.objects.create(meeting_key=1, meeting_name='Test GP', year=2024)
        self.session = Session.objects.create(session_key=1, meeting_key=1, name='Race', start_time=timezone.now())
        self.driver = Driver.objects.create(driver_number=1, full_name='Test Driver')
        self.entry = DriverEntry.objects.create(driver=self.driver, session_key=1, meeting=self.meeting)
        self.car = Car.objects.create(
            driver_number=1, session_key=1, meeting_key=1, date=timezone.now(),
            brake=100, drs=0, n_gear=5, rpm=10000, speed=200, throttle=80, is_manual=True
        )

    def test_show_main_redirect(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:show_main'))
        self.assertEqual(response.status_code, 302)

    def test_add_car_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:add_car'))
        self.assertEqual(response.status_code, 403)

    def test_add_car_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('car:add_car'))
        self.assertEqual(response.status_code, 200)

    def test_add_car_post_valid(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('car:add_car'), {
            'meeting_key': 1, 'session_key': 1, 'driver_number': 1, 'speed': 200,
            'throttle': 80, 'brake': 100, 'n_gear': 5, 'rpm': 10000, 'drs': 0, 'session_offset_seconds': 10
        })
        self.assertTrue(response.status_code in [200, 302])

    def test_show_json(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:show_json'))
        self.assertEqual(response.status_code, 200)

    def test_show_xml(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:show_xml'))
        self.assertEqual(response.status_code, 200)

    def test_show_json_by_id(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:show_json_by_id', args=[self.car.id]))
        self.assertEqual(response.status_code, 200)

    def test_show_xml_by_id(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:show_xml_by_id', args=[self.car.id]))
        self.assertEqual(response.status_code, 200)

    def test_all_cars_dashboard(self):
        response = self.client.get(reverse('car:list_page'))
        self.assertEqual(response.status_code, 200)

    def test_api_grouped_car_data(self):
        response = self.client.get(reverse('car:api_grouped'))
        self.assertEqual(response.status_code, 200)

    def test_edit_car_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:edit_car', args=[self.car.id]))
        self.assertEqual(response.status_code, 403)

    def test_edit_car_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('car:edit_car', args=[self.car.id]))
        self.assertEqual(response.status_code, 200)

    def test_edit_car_post_valid(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('car:edit_car', args=[self.car.id]), {
            'meeting_key': 1, 'session_key': 1, 'driver_number': 1, 'speed': 250,
            'throttle': 90, 'brake': 100, 'n_gear': 6, 'rpm': 12000, 'drs': 0, 'session_offset_seconds': 10
        })
        self.assertEqual(response.status_code, 302)

    def test_delete_car_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('car:delete_car', args=[self.car.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_car_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(reverse('car:delete_car', args=[self.car.id]))
        self.assertEqual(response.status_code, 302)

    def test_manual_list_admin_required(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('car:manual_list'))
        self.assertEqual(response.status_code, 403)

    def test_manual_list_admin_access(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('car:manual_list'))
        self.assertEqual(response.status_code, 200)

    def test_api_refresh_car_data_invalid_json(self):
        response = self.client.post(reverse('car:api_refresh'), data='invalid', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_api_refresh_car_data_no_meeting_key(self):
        response = self.client.post(reverse('car:api_refresh'), data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 400)
