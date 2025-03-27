from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View


# ✅ User Signup View
def signup(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("pass1")
        cpassword = request.POST.get("pass2")

        if password != cpassword:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')

        if User.objects.filter(username=email).exists():
            messages.info(request, 'Email already exists')
            return render(request, 'signup.html')

        # Create User
        user = User.objects.create_user(username=email, email=email, password=password, is_staff=True)
        user.is_active = False  # User must activate their account
        user.save()

        # Generate Activation Token
        token = default_token_generator.make_token(user)

        # Send Activation Email
        email_subject = "Activate Your Account"
        message = render_to_string('activate.html', {
            'user': user,
            'domain': '127.0.0.1:8000',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token
        })

        email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email])
        email_message.send()

        messages.success(request, 'Activate your account using the link sent to your email.')
        return redirect('/auth/login/')

    return render(request, 'signup.html')


# ✅ Activate User Account View
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Account activated successfully! You can now log in.')
            return redirect('/auth/login')

        return render(request, 'activatefail.html')


# ✅ Login View
def handlelogin(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('pass1')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('/')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('/auth/login')

    return render(request, 'login.html')


# ✅ Logout View
def handlelogout(request):
    logout(request)
    messages.info(request, "Logged out successfully")
    return redirect('/auth/login')


# ✅ Password Reset Request View
class RequestResetEmailView(View):
    def get(self, request):
        return render(request, 'request-reset-email.html')

    def post(self, request):
        email = request.POST['email']
        user = User.objects.filter(email=email)

        if user.exists():
            token = default_token_generator.make_token(user[0])

            # Send Reset Password Email
            email_subject = "Reset Your Password"
            message = render_to_string('reset-user-password.html', {
                'domain': '127.0.0.1:8000',
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': token
            })

            email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email])
            email_message.send()

            messages.info(request, "We have sent you an email with password reset instructions.")
            return render(request, 'request-reset-email.html')

        messages.error(request, "Email not found.")
        return render(request, 'request-reset-email.html')


# ✅ Set New Password View
class SetNewPasswordView(View):
    def get(self, request, uidb64, token):
        context = {'uidb64': uidb64, 'token': token}

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            if not default_token_generator.check_token(user, token):
                messages.warning(request, "Password reset link is invalid")
                return render(request, 'request-reset-email.html')

        except DjangoUnicodeDecodeError:
            messages.error(request, "Something went wrong")
            return render(request, 'request-reset-email.html')

        return render(request, 'set-new-password.html', context)

    def post(self, request, uidb64, token):
        context = {'uidb64': uidb64, 'token': token}

        password = request.POST['pass1']
        confirm_password = request.POST['pass2']

        if password != confirm_password:
            messages.warning(request, "Passwords do not match")
            return render(request, 'set-new-password.html', context)

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()

            messages.success(request, "Password reset successful! Please log in with your new password.")
            return redirect("/auth/login/")

        except DjangoUnicodeDecodeError:
            messages.error(request, "Something went wrong")
            return render(request, 'set-new-password.html', context)

        return render(request, 'set-new-password.html', context)
