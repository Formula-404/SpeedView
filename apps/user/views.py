from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, EditProfileForm, ChangePasswordForm, DeleteAccountForm
from .models import UserProfile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(id=user, role='user', theme_preference='dark')
            messages.success(request, 'Registration successful! Please login.')
            return redirect('user:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

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

@login_required
def logout_view(request):
    logout(request)
    return redirect('main:show_main')

def register_admin_view(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(id=user, role='admin', theme_preference='dark')
            messages.success(request, 'Admin registration successful! Please login.')
            return redirect('user:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'register_admin.html', {'form': form})

@login_required
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
                    messages.error(request, error)
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
