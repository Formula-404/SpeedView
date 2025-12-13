from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import IntegrityError
from .forms import RegisterForm, LoginForm, EditProfileForm, ChangePasswordForm, DeleteAccountForm
from .models import UserProfile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from django.contrib.auth.models import User

@require_http_methods(["GET", "POST"])
@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(id=user, role='user', theme_preference='dark')
                messages.success(request, 'Registration successful! Please login.')
                return redirect('user:login')
            except IntegrityError:
                messages.error(request, 'Username already exists. Please choose a different username.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('main:show_main')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('main:show_main')

@require_http_methods(["GET", "POST"])
@csrf_protect
def register_admin_view(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(id=user, role='admin', theme_preference='dark')
                messages.success(request, 'Admin registration successful! Please login.')
                return redirect('user:login')
            except IntegrityError:
                messages.error(request, 'Username already exists. Please choose a different username.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'register_admin.html', {'form': form})

@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def profile_settings_view(request):
    user = request.user

    edit_form = EditProfileForm(user=user, initial={'username': user.username, 'email': user.email})
    password_form = ChangePasswordForm(user=user)
    delete_form = DeleteAccountForm(user=user)

    if request.method == 'POST':
        if 'edit_profile' in request.POST:
            edit_form = EditProfileForm(request.POST, user=user)
            if edit_form.is_valid():
                user.username = edit_form.cleaned_data['username']
                user.email = edit_form.cleaned_data['email']
                user.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('user:profile_settings')
            else:
                for field, errors in edit_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

        elif 'change_password' in request.POST:
            password_form = ChangePasswordForm(request.POST, user=user)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('user:profile_settings')
            else:
                for error in password_form.non_field_errors():
                    messages.error(request, str(error))
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

        elif 'delete_account' in request.POST:
            delete_form = DeleteAccountForm(request.POST, user=user)
            if delete_form.is_valid():
                username = user.username
                user.delete()
                messages.success(request, f'Account {username} has been deleted successfully.')
                return redirect('main:show_main')
            else:
                for field, errors in delete_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

    context = {
        'edit_form': edit_form,
        'password_form': password_form,
        'delete_form': delete_form,
        'user': user,
    }

    return render(request, 'profile_settings.html', context)

@csrf_exempt
def login_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # fallback kalau suatu saat dikirim form-encoded
            data = request.POST

        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse(
                {
                    'status': True,
                    'username': user.username,
                    'message': 'Login successful!',
                },
                status=200,
            )
        else:
            return JsonResponse(
                {
                    'status': False,
                    'message': 'Invalid username or password',
                },
                status=401,
            )

    return JsonResponse(
        {'status': False, 'message': 'Invalid request method'},
        status=400,
    )


@csrf_exempt
def register_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()
            
            errors = []
            
            if not username:
                errors.append('Username is required')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters')
            elif not re.match(r'^[\w.@+-]+$', username):
                errors.append('Username can only contain letters, numbers, and @/./+/-/_ characters')
            elif User.objects.filter(username=username).exists():
                errors.append('Username already exists')
            
            if not password:
                errors.append('Password is required')
            elif len(password) < 8:
                errors.append('Password must be at least 8 characters')
            
            if not email:
                errors.append('Email is required')
            elif '@' not in email or '.' not in email:
                errors.append('Please enter a valid email address')
            elif User.objects.filter(email=email).exists():
                errors.append('Email already exists')
            
            if errors:
                return JsonResponse({'status': False, 'message': ', '.join(errors)}, status=400)
            
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()
            UserProfile.objects.create(id=user, role='user', theme_preference='dark')
            
            return JsonResponse({'status': True, 'message': 'Registration successful!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=400)
    return JsonResponse({'status': False, 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def logout_flutter(request):
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'status': True, 'message': 'Logout successful!'}, status=200)
    return JsonResponse({'status': False, 'message': 'Not logged in'}, status=401)

@csrf_exempt
def get_user_profile(request):
    if request.user.is_authenticated:
        user = request.user
        try:
            profile = user.profile
            return JsonResponse({
                'status': True,
                'username': user.username,
                'email': user.email,
                'role': profile.role,
                'theme_preference': profile.theme_preference,
            }, status=200)
        except UserProfile.DoesNotExist:
            return JsonResponse({'status': False, 'message': 'Profile not found'}, status=404)
    return JsonResponse({'status': False, 'message': 'Not logged in'}, status=401)

@csrf_exempt
def edit_profile_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            user = request.user
            profile = user.profile
            
            username = data.get('username')
            email = data.get('email')
            theme_preference = data.get('theme_preference')
            
            if username:
                if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    return JsonResponse({'status': False, 'message': 'Username already exists'}, status=400)
                user.username = username
            
            if email is not None:
                user.email = email
            
            if theme_preference:
                profile.theme_preference = theme_preference
            
            user.save()
            profile.save()
            
            return JsonResponse({'status': True, 'message': 'Profile updated successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=400)
    return JsonResponse({'status': False, 'message': 'Invalid request or not logged in'}, status=400)


@csrf_exempt
def change_password_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            user = request.user
            
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if not user.check_password(old_password):
                return JsonResponse({'status': False, 'message': 'Incorrect current password'}, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({'status': False, 'message': 'New passwords do not match'}, status=400)
                
            if len(new_password) < 8:
                 return JsonResponse({'status': False, 'message': 'Password must be at least 8 characters'}, status=400)
            
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            
            return JsonResponse({'status': True, 'message': 'Password changed successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=400)
    return JsonResponse({'status': False, 'message': 'Invalid request or not logged in'}, status=400)

@csrf_exempt
def delete_account_flutter(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            user = request.user
            
            password = data.get('password')
            confirm_text = data.get('confirm_text')
            
            if not user.check_password(password):
                return JsonResponse({'status': False, 'message': 'Incorrect password'}, status=400)
            
            if confirm_text != 'DELETE':
                return JsonResponse({'status': False, 'message': 'Please type DELETE to confirm'}, status=400)
            
            user.delete()
            return JsonResponse({'status': True, 'message': 'Account deleted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=400)
    return JsonResponse({'status': False, 'message': 'Invalid request or not logged in'}, status=400)
