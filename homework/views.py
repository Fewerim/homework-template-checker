from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from homework.forms import RegisterForm, DemoHomeworkForm, ClassroomCreateForm, AddStudentsToClassForm
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
                user=user,
                role=form.cleaned_data["role"],
                last_name=form.cleaned_data["last_name"],
                first_name=form.cleaned_data["first_name"],
                patronymic=form.cleaned_data.get("patronymic", ""),
                birth_date=form.cleaned_data.get("birth_date"),
                # classroom здесь НЕ назначаем на регистрации, если не выбираешь класс
            )
            login(request, user)
            return redirect("profile")
    else:
        form = RegisterForm()

    return render(request, "homework/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("profile")
    else:
        form = AuthenticationForm(request)

    return render(request, "homework/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile_view(request):
    profile = request.user.profile

    teacher_classes = request.user.teacher_classrooms.all()
    student_class = profile.classroom  # один класс или None

    return render(request, "homework/profile.html", {
        "profile": profile,
        "teacher_classes": teacher_classes,
        "student_class": student_class,
    })


def profile_detail(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(Profile, user=user_obj)

    return render(request, "homework/profile_detail.html", {
        "profile": profile,
        "student_class": profile.classroom,
    })

@login_required
def classroom_add_students_view(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)

    if request.method == "POST":
        form = AddStudentsToClassForm(request.POST)
        if form.is_valid():
            users = form.cleaned_data["students"]
            for u in users:
                u.profile.classroom = classroom
                u.profile.save()
            return redirect("classroom_detail", pk=classroom.pk)
    else:
        form = AddStudentsToClassForm()

    return render(request, "homework/classroom_add_students.html", {
        "classroom": classroom,
        "form": form,
    })

@login_required
def classroom_detail_view(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)

    if request.method == "POST":
        form = AddStudentsToClassForm(request.POST)
        if form.is_valid():
            users = form.cleaned_data["students"]
            for u in users:
                u.profile.classroom = classroom
                u.profile.save()
            return redirect("classroom_detail", pk=classroom.pk)
    else:
        form = AddStudentsToClassForm()

    students = Profile.objects.filter(role="student", classroom=classroom).order_by("last_name", "first_name")
    teacher_profile = Profile.objects.filter(user=classroom.teacher).first()

    return render(request, "homework/classroom_detail.html", {
        "classroom": classroom,
        "teacher_profile": teacher_profile,
        "students": students,
        "form": form,
    })


@login_required
def homework_list_view(request):
    user = request.user
    profile = user.profile

    if profile.role == "teacher":
        classrooms = Classroom.objects.filter(teacher=user)
    else:
        classrooms = Classroom.objects.filter(pk=profile.classroom_id) if profile.classroom_id else Classroom.objects.none()

    homeworks = HomeworkTemplate.objects.filter(classroom__in=classrooms).distinct()

    return render(request, "homework/homework_list.html", {
        "homeworks": homeworks,
        "profile": profile,
    })


@login_required
@transaction.atomic
def classroom_create(request):
    if request.user.profile.role != "teacher":
        return redirect("home")

    if request.method == "POST":
        form = ClassroomCreateForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.teacher = request.user
            classroom.save()

            selected_students = form.cleaned_data.get("students")
            if selected_students:
                Profile.objects.filter(user__in=selected_students, role="student").update(classroom=classroom)

            return redirect("profile")
    else:
        form = ClassroomCreateForm()

    return render(request, "homework/classroom_create.html", {"form": form})
