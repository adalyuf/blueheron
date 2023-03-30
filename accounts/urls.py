from django.urls import path
from accounts import views
from django.contrib.auth.views import PasswordResetConfirmView
from allauth.account.views import SignupView, LoginView

urlpatterns = [
    path("signup/", SignupView.as_view(template_name='pages/auth/basic-signup.html'), name="signup"),
    path("login/", LoginView.as_view(template_name='pages/auth/basic-login.html'), name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("password_reset/", views.password_reset, name="password_reset"),
    path("password_reset/sent/", views.password_reset_sent, name="password_reset_sent"),
    path("password_reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(template_name='pages/auth/password_reset_confirm.html') , name="password_reset_confirm"),
    path("password_reset/complete/", views.password_reset_complete, name="password_reset_complete"),

]