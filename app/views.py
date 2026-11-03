from django.shortcuts import render,redirect
from .models import Home,Category
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
import random
from django.core.mail import send_mail
# Create your views here.

def home(request,id=False):
    if id:
        catobject=Category.objects.get(id=id)
        product=Home.objects.filter(category=catobject)
    else:
        product = Home.objects.all()
    
    category = Category.objects.all()
    return render(request,'home.html',{'product':product,'category':category})


def details(request,id):
    detail = Home.objects.get(id=id)
    return render(request,'details.html',{'detail':detail})


def signin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username,password)
        user = authenticate(
            request,username=username,password=password
        )
        if user is not None:
            login(request,user)
            return redirect("home")
        messages.error(request,"Invalid username or password")
    return render(request,'login.html')

def signout(request):
    logout(request)
    return redirect("login")

def signup(request):
    if request.method == "POST":
        username=request.POST.get("username")
        email=request.POST.get("email")
        password=request.POST.get("password")
        confirm_password=request.POST.get("password2")
        # print(username,password,email,confirm_password,sep="\n")
        if password!=confirm_password:
            messages.error(request,"wrong password")
            return redirect("signup")
        elif User.objects.filter(username=username).exists():
            messages.error(request,"username already exists")
            return redirect("signup")
        elif User.objects.filter(email=email).exists():
            messages.error(request,"email already exists")
            return redirect("signup")

        otp=random.randint(100000,999999)
        request.session["signup_username"]=username
        request.session["signup_email"]=email
        request.session["signup_password"]=password
        request.session["signup_otp"]=otp
        print(f"OTP={otp}")
        send_mail(
            "OTP Verification",
            f"your otp is {otp}",
            "bibin7301@gmail.com",
            [email],
            fail_silently=False
        )
        return redirect("otp")

    return render(request,'signup.html')


def otp(request):
    if request.method=="POST":
        enter_otp = request.POST.get("otp")
        session_otp=request.session.get("signup_otp")

        if enter_otp==str(session_otp):
            username=request.session.get("signup_username")
            email=request.session.get("signup_email")
            password=request.session.get("signup_password")
            user=User.objects.create_user(username=username,email=email,password=password)


            request.session.pop("signup_otp",None)
            request.session.pop("signup_username",None)
            request.session.pop("signup_email",None)
            request.session.pop("signup_password",None)
            messages.success(request,"user created successfully")
            login(request,user)
            return redirect("home")
    
    return render(request,'otp.html')


def resend(request):
    

    otp=random.randint(100000,999999)
    request.session["signup_otp"]=otp
    email=request.session.get("signup_email")
    send_mail(
            "OTP Verification",
            f"your otp is {otp}",
            "bibin7301@gmail.com",
            [email],
            fail_silently=False
            )
    return redirect("otp")










# ================= FORGOT PASSWORD =================

def forgot(request):

    if request.method == "POST":

        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:

            messages.error(
                request,
                "No account found with this email."
            )

            return redirect("forgot")

        forgot_otp = random.randint(100000, 999999)

        request.session["forgot_otp"] = str(forgot_otp)
        request.session["forgot_email"] = email

        # Send OTP to email
        send_mail(
            subject="Goods - Password Reset OTP",
            message=f"""
Hello {user.username},

Your OTP for resetting your Goods account password is:

{forgot_otp}

This OTP is required to reset your password.

If you did not request a password reset, please ignore this email.

Regards,
Goods Team
""",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("forgot_otp")

    return render(request, "forgot.html")


# ================= FORGOT PASSWORD OTP =================

def forgot_otp(request):

    session_otp = request.session.get("forgot_otp")

    if not session_otp:

        messages.error(
            request,
            "OTP expired. Please try again."
        )

        return redirect("forgot")

    if request.method == "POST":

        entered_otp = request.POST.get("enter_otp")

        if entered_otp == session_otp:

            # OTP verified
            request.session["forgot_verified"] = True

            request.session.pop("forgot_otp", None)

            return redirect("reset_password")

        else:

            messages.error(
                request,
                "Invalid OTP."
            )

            return redirect("forgot_otp")

    return render(request, "forgot_otp.html")


# ================= RESET PASSWORD =================

def reset_password(request):

    # Check whether OTP was verified
    if not request.session.get("forgot_verified"):

        messages.error(
            request,
            "Please verify the OTP first."
        )

        return redirect("forgot")

    if request.method == "POST":

        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        # Check passwords
        if password != password2:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("reset_password")

        email = request.session.get("forgot_email")

        try:

            user = User.objects.get(email=email)

        except User.DoesNotExist:

            messages.error(
                request,
                "User not found."
            )

            return redirect("forgot")

        # Change password
        user.set_password(password)
        user.save()

        # Clear session
        request.session.pop("forgot_email", None)
        request.session.pop("forgot_verified", None)

        messages.success(
            request,
            "Password changed successfully. Please login."
        )

        return redirect("login")

    return render(request, "reset_password.html")

                    
         


