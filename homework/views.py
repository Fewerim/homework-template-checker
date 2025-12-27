from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from homework.forms import RegisterForm
from homework.models import Profile


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            Profile.objects.create(
                user = user,
                role = form.cleaned_data["role"],
                last_name = form.cleaned_data["last_name"],
                first_name = form.cleaned_data["first_name"],
                patronymic = form.cleaned_data.get("patronymic", ""),
                birth_date = form.cleaned_data.get("birth_date"),
            )
            login(request, user)
            return redirect("profile")
    else:
        form = RegisterForm()
    return render(request, "homework/register.html", {"form" : form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
        return redirect("profile")
    else:
        form = AuthenticationForm(request)
    return render(request, "homework/login.html", {"form" : form})


@login_required
def profile_view(request):
    profile = request.user.profile
    teacher_classes = request.user.teacher_classrooms.all()
    student_classes = request.user.classrooms.all()
    context = {
        "profile": profile,
        "teacher_classes": teacher_classes,
        "student_classes": student_classes,
    }
    return render(request, "homework/profile.html", context)


def logout_view(request):
    logout(request)
    return redirect("home")

