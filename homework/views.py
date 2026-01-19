from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404

from homework.forms import RegisterForm, DemoHomeworkForm
from homework.models import Profile, Classroom, HomeworkTemplate


DEMO_QUESTIONS = [
    "2 + 2 = ?",
    "Столица Франции?",
    "Назови 1 язык программирования.",
]

def home_view(request):
    if request.method == "POST":
        form = DemoHomeworkForm(request.POST)
        if form.is_valid():
            return render(request, "homework/homework_demo.html", {
                "form": form,
                "demo_questions": DEMO_QUESTIONS,
                "submitted": True,
            })
    else:
        form = DemoHomeworkForm()

    return render(request, "homework/homework_demo.html", {
        "form": form,
        "demo_questions": DEMO_QUESTIONS,
    })

def homework_demo_view(request):
    return render(request, "homework/homework_demo.html")


def register_view(request):
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



def logout_view(request):
    logout(request)
    return redirect("home")


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


@login_required
def classroom_detail_view(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)

    students = Profile.objects.filter(user__in=classroom.students.all())

    teacher_profile = Profile.objects.filter(user=classroom.teacher).first()

    context = {
        "classroom": classroom,
        "students": students,
        "teacher_profile": teacher_profile,
    }
    return render(request, "homework/classroom_detail.html", context)


@login_required
def homework_list_view(request):
    user = request.user

    if user.profile.role == "teacher":
        classrooms = Classroom.objects.filter(teacher=user)
    else:
        classrooms = Classroom.objects.filter(students=user)

    homeworks = HomeworkTemplate.objects.filter(classroom__in=classrooms).distinct()
    context = {"homeworks": homeworks}

    return render(request, "homework/homework_list.html", context)

