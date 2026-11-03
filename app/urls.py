from django.urls import path
from . import views

urlpatterns =[
    path('',views.home, name='home'),
    path("details/<int:id>",views.details,name='details'),
    path("login/",views.signin,name='login'),
    path("signup/",views.signup,name='signup'),
    path("logout/",views.signout,name='logout'),
    path("category/<int:id>",views.home, name='category'),
    path("otp/",views.otp,name='otp'),
    path("resend/",views.resend,name='resend'),
    path("forgot/", views.forgot, name="forgot"),
    path("forgot-otp/", views.forgot_otp, name="forgot_otp"),
    path("reset-password/", views.reset_password, name="reset_password")
]