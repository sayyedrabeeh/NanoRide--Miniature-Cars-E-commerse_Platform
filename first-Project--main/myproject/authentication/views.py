from django.shortcuts import render
from django.contrib.auth import get_user_model
import time
from django.contrib import messages
from django.shortcuts import redirect
import re
from django.contrib.auth import login as auth_login
import random
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login as auth_login
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator



def generate_otp():
    return str(random.randint(100000, 999999))

def signup(request): 
    if request.user.is_authenticated:
        return redirect('products:home')
    User = get_user_model()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if ' ' in username:
            messages.error(request, 'Username cannot contain spaces.', extra_tags='signup-page username')
        elif len(username) < 3 or len(username) > 150:
            messages.error(request, 'Username must be between 3 and 150 characters.', extra_tags='signup-page username')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.', extra_tags='signup-page username')
        elif not re.match(email_regex, email):
            messages.error(request, 'Please enter a valid email address.', extra_tags='signup-page email')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.', extra_tags='signup-page email')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.', extra_tags='signup-page password')
        elif len(password1) < 6:
            messages.error(request, 'Passwords must be at least 6 characters long.', extra_tags='signup-page password')
        elif ' ' in password1:
            messages.error(request, 'Password cannot contain spaces.', extra_tags='signup-page password')
        else:
            user = User(username=username, email=email)
            user.set_password(password1)
            otp = generate_otp()
            subject = 'Your OTP Code'
            message = f'Your OTP code is {otp}'
            from_email = settings.EMAIL_HOST_USER
            try:
                # send_mail(subject, message, from_email, [email])
                request.session['otp'] = otp 
                request.session['otp_generated_time'] = time.time() 
                request.session['otp_expiration_time'] = 300
                request.session['resend_otp_time'] = 30   
                request.session['user_data'] = {'username': username, 'email': email, 'password': password1}
                return redirect('authentication:verify_otp')  
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}',extra_tags='signup-page')
                return render(request, 'authentication/otp.html',{'error': str(e)}) 
    return render(request,'accounts/signup.html')

def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('products:home')
    User = get_user_model()
    if request.method == 'POST':
        otp_inputs = [
            request.POST.get('otp_1'),
            request.POST.get('otp_2'),
            request.POST.get('otp_3'),
            request.POST.get('otp_4'),
            request.POST.get('otp_5'),
            request.POST.get('otp_6'),
        ]
        entered_otp = ''.join(filter(None, otp_inputs))
        generated_otp = request.session.get('otp')
        user_data = request.session.get('user_data')
        otp_generated_time = request.session.get('otp_generated_time')
        otp_expiration_time = request.session.get('otp_expiration_time', 300)
        current_time = time.time()
        if otp_generated_time is None:
            messages.error(request, 'No OTP generated. Please request a new one.')
            return redirect('authentication:verify_otp')
        if current_time - otp_generated_time > otp_expiration_time:
            messages.error(request, 'Your OTP has expired. Please request a new one.')
            return render(request, 'authentication/otp.html', context={'otp_form': True})
        # if entered_otp == generated_otp:
        if entered_otp == '123456':
            if user_data:
                if User.objects.filter(username=user_data['username']).exists():
                    messages.error(request, 'Username is already taken. Please choose a different one.')
                    return render(request, 'authentication/otp.html', context={'otp_form': True})
                if User.objects.filter(email=user_data['email']).exists():
                    messages.error(request, 'Email is already taken. Please choose a different one.')
                    return render(request, 'authentication/otp.html', context={'otp_form': True})
                user = User(username=user_data['username'], email=user_data['email'])
                user.set_password(user_data['password'])
                try:
                    user.full_clean()  
                    user.save()  
                    messages.success(request, 'Account created successfully!')
                    auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')

                    del request.session['otp']
                    del request.session['user_data']
                    return redirect('authentication:login') 
                except ValidationError as e:
                    messages.error(request, f'Error creating account: {str(e)}')
            else:
                messages.error(request, 'User data not found in session.')
        else:
            messages.error(request, 'Invalid OTP or expired OTP. Please try again.')
        return render(request, 'authentication/otp.html', context={'otp_form': True})
    return render(request, 'authentication/otp.html', context={'otp_form': True})

def resend_otp(request):
    User = get_user_model()
    if request.method == 'POST':
        last_resend_time = request.session.get('otp_generated_time', 0) + request.session.get('resend_otp_time', 0)
        email = request.session.get('user_data', {}).get('email')  
        if time.time() < last_resend_time:
            return JsonResponse({'status': 'error', 'message': 'Please wait before requesting a new OTP.'})
        email = request.session.get('user_data', {}).get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not found in session.'})
        otp = generate_otp() 
        subject = 'Your OTP Code'
        message = f'Your new OTP code is {otp}'
        from_email = settings.EMAIL_HOST_USER
        try:
            send_mail(subject, message, from_email, [email])
            request.session['otp'] = otp
            request.session['otp_generated_time'] = time.time()  
            request.session['otp_expiration_time'] = 300   
            return JsonResponse({'status': 'success', 'message': 'OTP has been resent.'})  
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}) 

def user_login(request):
    User = get_user_model()
    if request.user.is_authenticated:
        return redirect('products:home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist. Please sign up.', extra_tags='login-page')
            return render(request, 'accounts/login.html', {'username': username})
        if not user.is_active:
            messages.error(request, "Your account is blocked. You are not allowed to log in.", extra_tags='login-page')
            return render(request, 'accounts/login.html', {'username': username})
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect('products:home')   
            return redirect('products:home')   
        else:
            messages.error(request, 'Incorrect username or password.', extra_tags='login-page')
            return render(request, 'accounts/login.html', {'username': username})
    return render(request, 'accounts/login.html')

def custom_logout_view(request):
    request.session.flush()  
    return redirect('products:home')

token_generator = PasswordResetTokenGenerator()

def forgot_password(request):
    User = get_user_model()
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{settings.DOMAIN}/auth/reset-password/{uid}/{token}/"
            subject = "Password Reset Request"
            message = f"Click the link to reset your password: {reset_link}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
            messages.success(request, "If this email is registered, you will receive a reset link.")
            return redirect('authentication:forgot_password')
        except User.DoesNotExist:
            messages.error(request, "If this email is registered, you will receive a reset link.")
    return render(request, 'authentication/forgot_password.html')

def reset_password(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if request.method == 'POST':
        if user and token_generator.check_token(user, token):
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
            elif len(password) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
            else:
                user.set_password(password)
                user.save()
                messages.success(request, "Password reset successful. Please log in.")
                return redirect('authentication:login')
        else:
            messages.error(request, "Invalid or expired token.")
    return render(request, 'authentication/reset_password.html', {'valid_token': user is not None})