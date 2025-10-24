from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile
from .forms import RegisterForm, LoginForm, EditProfileForm, ChangePasswordForm, DeleteAccountForm


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@test.com')
        self.profile = UserProfile.objects.create(id=self.user, role='user', theme_preference='dark')

    def test_user_profile_all_features(self):
        self.assertEqual(self.profile.id, self.user)
        self.assertEqual(self.profile.role, 'user')
        self.assertEqual(self.profile.theme_preference, 'dark')
        self.assertEqual(str(self.profile), 'testuser - user')
        self.assertEqual(UserProfile._meta.db_table, 'user_profile')

        self.profile.role = 'admin'
        self.profile.theme_preference = 'light'
        self.profile.save()
        self.assertEqual(self.profile.role, 'admin')
        self.assertEqual(self.profile.theme_preference, 'light')

        user_id = self.user.id
        self.user.delete()
        self.assertFalse(UserProfile.objects.filter(id=user_id).exists())


class FormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@test.com')

    def test_register_form(self):
        form = RegisterForm(data={'username': 'newuser', 'email': 'new@test.com', 'password1': 'testpass123', 'password2': 'testpass123'})
        self.assertTrue(form.is_valid())

        User.objects.create_user(username='existing', email='existing@test.com', password='testpass123')
        form = RegisterForm(data={'username': 'new', 'email': 'existing@test.com', 'password1': 'testpass123', 'password2': 'testpass123'})
        self.assertFalse(form.is_valid())
        self.assertIn('Email already exists', form.errors['email'])

        form = RegisterForm(data={'username': 'existing', 'email': 'new2@test.com', 'password1': 'testpass123', 'password2': 'testpass123'})
        self.assertFalse(form.is_valid())
        self.assertIn('Username already exists', form.errors['username'])

    def test_login_form(self):
        form = LoginForm(data={'username': 'testuser', 'password': 'testpass123'})
        self.assertTrue(form.is_valid())

        form = LoginForm(data={'password': 'testpass123'})
        self.assertFalse(form.is_valid())

    def test_edit_profile_form(self):
        form = EditProfileForm(data={'username': 'newname', 'email': 'new@test.com'}, user=self.user)
        self.assertTrue(form.is_valid())

        form = EditProfileForm(data={'username': 'testuser', 'email': 'test@test.com'}, user=self.user)
        self.assertTrue(form.is_valid())

        other = User.objects.create_user(username='other', password='testpass123', email='other@test.com')
        form = EditProfileForm(data={'username': 'other', 'email': 'test@test.com'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Username already exists', form.errors['username'])

        form = EditProfileForm(data={'username': 'testuser', 'email': 'other@test.com'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Email already exists', form.errors['email'])

    def test_change_password_form(self):
        form = ChangePasswordForm(data={'old_password': 'testpass123', 'new_password1': 'newpass123', 'new_password2': 'newpass123'}, user=self.user)
        self.assertTrue(form.is_valid())

        form = ChangePasswordForm(data={'old_password': 'wrongpass', 'new_password1': 'newpass123', 'new_password2': 'newpass123'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Current password is incorrect', form.errors['old_password'])

        form = ChangePasswordForm(data={'old_password': 'testpass123', 'new_password1': 'newpass123', 'new_password2': 'different'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('New passwords do not match', form.non_field_errors())

        form = ChangePasswordForm(data={'old_password': 'testpass123', 'new_password1': 'short', 'new_password2': 'short'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Password must be at least 8 characters', form.non_field_errors())

    def test_delete_account_form(self):
        form = DeleteAccountForm(data={'password': 'testpass123', 'confirm_text': 'DELETE'}, user=self.user)
        self.assertTrue(form.is_valid())

        form = DeleteAccountForm(data={'password': 'wrongpass', 'confirm_text': 'DELETE'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Password is incorrect', form.errors['password'])

        form = DeleteAccountForm(data={'password': 'testpass123', 'confirm_text': 'delete'}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("You must type 'DELETE' exactly to confirm", form.errors['confirm_text'])



class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='test@test.com')
        self.profile = UserProfile.objects.create(id=self.user, role='user', theme_preference='dark')

    def test_register_view(self):
        response = self.client.get(reverse('user:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

        response = self.client.post(reverse('user:register'), {'username': 'newuser', 'email': 'new@test.com', 'password1': 'testpass123', 'password2': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserProfile.objects.filter(id__username='newuser', role='user').exists())

        response = self.client.post(reverse('user:register'), {'username': 'bad', 'email': 'bad@test.com', 'password1': 'pass1', 'password2': 'pass2'})
        self.assertEqual(response.status_code, 200)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:register'))
        self.assertEqual(response.status_code, 302)

    def test_login_view(self):
        response = self.client.get(reverse('user:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

        response = self.client.post(reverse('user:login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        response = self.client.post(reverse('user:login'), {'username': 'testuser', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, 200)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:login'))
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:logout'))
        self.assertEqual(response.status_code, 302)

        self.client.logout()
        response = self.client.get(reverse('user:logout'))
        self.assertEqual(response.status_code, 302)

    def test_register_admin_view(self):
        response = self.client.get(reverse('user:register_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register_admin.html')

        response = self.client.post(reverse('user:register_admin'), {'username': 'admin', 'email': 'admin@test.com', 'password1': 'testpass123', 'password2': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserProfile.objects.filter(id__username='admin', role='admin').exists())

        response = self.client.post(reverse('user:register_admin'), {'username': 'bad', 'email': 'bad@test.com', 'password1': 'pass1', 'password2': 'pass2'})
        self.assertEqual(response.status_code, 200)

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:register_admin'))
        self.assertEqual(response.status_code, 302)

    def test_profile_settings_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user:profile_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_settings.html')

        self.client.logout()
        response = self.client.get(reverse('user:profile_settings'))
        self.assertEqual(response.status_code, 302)

    def test_profile_settings_edit_profile(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('user:profile_settings'), {'edit_profile': '', 'username': 'newname', 'email': 'new@test.com'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')

        other = User.objects.create_user(username='other', password='testpass123', email='other@test.com')
        response = self.client.post(reverse('user:profile_settings'), {'edit_profile': '', 'username': 'other', 'email': 'new@test.com'})
        self.assertEqual(response.status_code, 200)

    def test_profile_settings_change_password(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('user:profile_settings'), {'change_password': '', 'old_password': 'testpass123', 'new_password1': 'newpass123', 'new_password2': 'newpass123'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

        response = self.client.post(reverse('user:profile_settings'), {'change_password': '', 'old_password': 'wrongpass', 'new_password1': 'newpass123', 'new_password2': 'newpass123'})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('user:profile_settings'), {'change_password': '', 'old_password': 'newpass123', 'new_password1': 'pass1', 'new_password2': 'pass2'})
        self.assertEqual(response.status_code, 200)

    def test_profile_settings_delete_account(self):
        user2 = User.objects.create_user(username='user2', password='testpass123', email='user2@test.com')
        self.client.login(username='user2', password='testpass123')
        response = self.client.post(reverse('user:profile_settings'), {'delete_account': '', 'password': 'testpass123', 'confirm_text': 'DELETE'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='user2').exists())

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('user:profile_settings'), {'delete_account': '', 'password': 'wrongpass', 'confirm_text': 'DELETE'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='testuser').exists())

        response = self.client.post(reverse('user:profile_settings'), {'delete_account': '', 'password': 'testpass123', 'confirm_text': 'delete'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='testuser').exists())