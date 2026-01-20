import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from homework.forms import (
    RegisterForm, DemoHomeworkForm, ClassroomCreateForm, AddStudentsToClassForm,
    HomeworkTemplateCreateForm, QuestionFormSet, AnswerFormSet, ReviewAnswerFormSet, SubmissionScoreForm
)
from homework.models import Profile, Classroom, HomeworkTemplate, GradeScale, StudentSubmission


DEMO_QUESTIONS = [
    "2 + 2 = ?",
    "Столица Франции?",
    "Назови 1 язык программирования.",
]

BASE_ROLE = "student"


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


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                role=BASE_ROLE,
                last_name=form.cleaned_data["last_name"],
                first_name=form.cleaned_data["first_name"],
                patronymic=form.cleaned_data.get("patronymic", ""),
                birth_date=form.cleaned_data.get("birth_date"),
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
        form = AuthenticationForm()

    return render(request, "homework/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")


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
def profile_view(request):
    profile = request.user.profile
    teacher_classes = request.user.teacher_classrooms.all()
    student_class = profile.classroom

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
def homework_create_view(request, classroom_id):
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    if classroom.teacher_id != request.user.id:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = HomeworkTemplateCreateForm(request.POST, request.FILES)
        formset = QuestionFormSet(request.POST, prefix="q")

        if form.is_valid() and formset.is_valid():
            grade_scale = GradeScale.objects.first()
            if grade_scale is None:
                form.add_error(None, "В системе нет шкалы оценивания. Создайте её в админке.")
            else:
                hw = form.save(commit=False)
                hw.classroom = classroom
                hw.grade_scale = grade_scale

                questions = []
                correct = {}

                for row in formset.cleaned_data:
                    if not row or row.get("DELETE"):
                        continue

                    num = row["number"]
                    fmt = row["answer_format"]
                    ca = (row["correct_answer"] or "").strip()

                    questions.append({
                        "number": num,
                        "answer_format": fmt,
                    })
                    correct[str(num)] = ca

                questions.sort(key=lambda x: x["number"])

                hw.questions = questions
                hw.correct_answers = correct
                hw.save()

                return redirect("classroom_detail", pk=classroom.id)
    else:
        form = HomeworkTemplateCreateForm()
        formset = QuestionFormSet(prefix="q")

    return render(request, "homework/homework_create.html", {
        "classroom": classroom,
        "form": form,
        "formset": formset,
    })


@login_required
def homework_detail_view(request, hw_id):
    hw = get_object_or_404(HomeworkTemplate, pk=hw_id)

    profile = getattr(request.user, "profile", None)
    if profile is None:
        return HttpResponseForbidden()

    if profile.role == "teacher":
        if hw.classroom.teacher_id != request.user.id:
            return HttpResponseForbidden()

        students = (
            Profile.objects
            .filter(role="student", classroom=hw.classroom)
            .select_related("user")
            .order_by("last_name", "first_name")
        )

        submissions = StudentSubmission.objects.filter(homework_template=hw).select_related("student")
        sub_by_user_id = {s.student_id: s for s in submissions}

        rows = []
        for st in students:
            sub = sub_by_user_id.get(st.user_id)
            rows.append({
                "student_profile": st,
                "submitted": sub is not None,
                "submission": sub,
            })

        return render(request, "homework/homework_detail_teacher.html", {
            "hw": hw,
            "rows": rows,
        })

    if profile.role == "student":
        if profile.classroom_id != hw.classroom_id:
            return HttpResponseForbidden()
        return redirect("homework_submit", hw_id=hw.id)

    return HttpResponseForbidden()


@login_required
def homework_submit_view(request, hw_id):
    hw = get_object_or_404(HomeworkTemplate, pk=hw_id)

    if not hasattr(request.user, "profile") or request.user.profile.role != "student":
        return HttpResponseForbidden()
    if request.user.profile.classroom_id != hw.classroom_id:
        return HttpResponseForbidden()

    submission = StudentSubmission.objects.filter(
        homework_template=hw, student=request.user
    ).first()

    initial = [{"number": q["number"]} for q in (hw.questions or [])]

    if request.method == "POST":
        formset = AnswerFormSet(request.POST, prefix="a", initial=initial)
        if formset.is_valid():
            answers = {}
            for row in formset.cleaned_data:
                num = row["number"]
                answers[str(num)] = (row["answer"] or "").strip()

            correct_map = hw.correct_answers or {}
            auto_score = 0

            def get_correct(num):
                if isinstance(correct_map, dict):
                    return correct_map.get(str(num)) or correct_map.get(num) or ""
                return ""

            for q in (hw.questions or []):
                num = q["number"]
                fmt = q.get("answer_format", "text")

                stud = (answers.get(str(num)) or answers.get(num) or "").strip()
                corr = (get_correct(num) or "").strip()

                if fmt == "text":
                    if stud.casefold() == corr.casefold():
                        auto_score += 1
                elif fmt == "int":
                    try:
                        if int(stud) == int(corr):
                            auto_score += 1
                    except (TypeError, ValueError):
                        pass
                elif fmt == "float":
                    try:
                        s = float(stud.replace(",", "."))
                        c = float(corr.replace(",", "."))
                        if abs(s - c) < 1e-6:
                            auto_score += 1
                    except (TypeError, ValueError):
                        pass

            if submission is None:
                submission = StudentSubmission.objects.create(
                    student=request.user,
                    homework_template=hw,
                    answers=answers,
                    auto_score=auto_score,
                    final_score=auto_score,
                    graded=False,
                )
            else:
                submission.answers = answers
                submission.auto_score = auto_score
                submission.final_score = auto_score
                submission.graded = False
                submission.save()

            return redirect("homework_list")
    else:
        if submission:
            initial = [{"number": q["number"], "answer": (submission.answers or {}).get(str(q["number"]), "")}
                       for q in (hw.questions or [])]
        formset = AnswerFormSet(prefix="a", initial=initial)

    return render(request, "homework/homework_submit.html", {
        "hw": hw,
        "formset": formset,
        "submission": submission,
    })


@login_required
def submission_review_view(request, hw_id, user_id):
    hw = get_object_or_404(HomeworkTemplate, pk=hw_id)

    if hw.classroom.teacher_id != request.user.id:
        return HttpResponseForbidden()

    student_profile = get_object_or_404(
        Profile, user_id=user_id, role="student", classroom=hw.classroom
    )

    submission = StudentSubmission.objects.filter(
        homework_template=hw,
        student=student_profile.user
    ).first()

    if submission is None:
        submission = StudentSubmission(
            homework_template=hw,
            student=student_profile.user,
            answers={},
            auto_score=0,
            final_score=0,
            graded=False,
        )

    initial_rows = [
        {
            "number": q["number"],
            "answer": (submission.answers or {}).get(str(q["number"]), ""),
        }
        for q in (hw.questions or [])
    ]

    if request.method == "POST":
        formset = ReviewAnswerFormSet(request.POST, prefix="r", initial=initial_rows)
        score_form = SubmissionScoreForm(request.POST)

        if formset.is_valid() and score_form.is_valid():
            answers = {}
            for row in formset.cleaned_data:
                num = row["number"]
                answers[str(num)] = (row["answer"] or "").strip()

            auto_score = _calc_auto_score(hw, answers)
            final_score = score_form.cleaned_data["final_score"]

            if submission.pk is None:
                submission = StudentSubmission.objects.create(
                    homework_template=hw,
                    student=student_profile.user,
                    answers=answers,
                    auto_score=auto_score,
                    final_score=final_score,
                    graded=True,
                )
            else:
                submission.answers = answers
                submission.auto_score = auto_score
                submission.final_score = final_score
                submission.graded = True
                submission.save()

            return redirect("homework_detail", hw_id=hw.id)
    else:
        formset = ReviewAnswerFormSet(prefix="r", initial=initial_rows)
        score_form = SubmissionScoreForm(initial={"final_score": submission.final_score})

    return render(request, "homework/submission_review.html", {
        "hw": hw,
        "student_profile": student_profile,
        "submission": submission,
        "formset": formset,
        "score_form": score_form,
    })


def _calc_auto_score(hw, answers):
    correct_map = hw.correct_answers or {}
    auto_score = 0

    def get_correct(num):
        if isinstance(correct_map, dict):
            return correct_map.get(str(num)) or correct_map.get(num) or ""
        return ""

    for q in (hw.questions or []):
        num = q["number"]
        fmt = q.get("answer_format", "text")

        stud = (answers.get(str(num)) or answers.get(num) or "").strip()
        corr = (get_correct(num) or "").strip()

        if fmt == "text":
            if stud.casefold() == corr.casefold():
                auto_score += 1
        elif fmt == "int":
            try:
                if int(stud) == int(corr):
                    auto_score += 1
            except (TypeError, ValueError):
                pass
        elif fmt == "float":
            try:
                s = float(stud.replace(",", "."))
                c = float(corr.replace(",", "."))
                if abs(s - c) < 1e-6:
                    auto_score += 1
            except (TypeError, ValueError):
                pass

    return auto_score


@login_required
def student_progress_png(request, user_id: int):
    student = get_object_or_404(User, pk=user_id)

    qs = (
        StudentSubmission.objects
        .filter(student=student)
        .select_related("homework_template")
        .order_by("homework_template__deadline")
    )

    labels = [s.homework_template.title for s in qs]
    scores = [s.final_score for s in qs]
    max_scores = [s.homework_template.max_score for s in qs]

    fig, ax = plt.subplots(figsize=(10, 3))

    if scores:
        ax.plot(range(len(scores)), scores, marker="o", label="Итог")
        ax.plot(range(len(max_scores)), max_scores, linestyle="--", label="Макс.")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=20, ha="right")
    else:
        ax.text(0.5, 0.5, "Нет сданных работ", ha="center", va="center")
        ax.set_xticks([])
        ax.set_yticks([])

    ax.set_title(f"Успеваемость ученика: {student.last_name} {student.first_name}")
    ax.set_ylabel("Баллы")
    ax.grid(True, alpha=0.3)
    ax.legend()

    response = HttpResponse(content_type="image/png")
    fig.tight_layout()
    fig.savefig(response, format="png")
    plt.close(fig)
    return response


@login_required
def my_progress_png(request):
    qs = (
        StudentSubmission.objects
        .filter(student=request.user)
        .select_related("homework_template")
        .order_by("homework_template__deadline")
    )

    labels = [s.homework_template.title for s in qs]
    scores = [s.final_score for s in qs]
    max_scores = [s.homework_template.max_score for s in qs]

    fig, ax = plt.subplots(figsize=(10, 3))

    if scores:
        ax.plot(range(len(scores)), scores, marker="o", label="Итог")
        ax.plot(range(len(max_scores)), max_scores, linestyle="--", label="Макс.")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=20, ha="right")
    else:
        ax.text(0.5, 0.5, "Нет сданных работ", ha="center", va="center")
        ax.set_xticks([])
        ax.set_yticks([])

    ax.set_title(f"Успеваемость ученика: {request.user.last_name} {request.user.first_name}")
    ax.set_ylabel("Баллы")
    ax.grid(True, alpha=0.3)
    ax.legend()

    response = HttpResponse(content_type="image/png")
    fig.tight_layout()
    fig.savefig(response, format="png")
    plt.close(fig)
    return response


@login_required
def homework_stats_png(request, hw_id: int):
    hw = get_object_or_404(HomeworkTemplate, pk=hw_id)

    mode = request.GET.get("mode", "bar")

    qs = (
        StudentSubmission.objects
        .filter(homework_template=hw)
        .select_related("student__profile")
        .order_by("-final_score")
    )

    fig, ax = plt.subplots(figsize=(10, 3.5))

    if not qs.exists():
        ax.text(0.5, 0.5, "Нет сданных работ", ha="center", va="center")
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        scores = [s.final_score for s in qs]

        if mode == "hist":
            bins = min(10, max(3, hw.max_score or 10))
            ax.hist(scores, bins=bins)
            ax.set_title(f"Распределение итоговых баллов: {hw.title}")
            ax.set_xlabel("Итоговый балл")
            ax.set_ylabel("Количество работ")
        else:
            names = [
                f"{s.student.profile.last_name} {s.student.profile.first_name}"
                for s in qs
            ]
            ax.bar(range(len(scores)), scores)
            ax.set_title(f"Кто сколько набрал: {hw.title}")
            ax.set_ylabel("Итоговый балл")
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(names, rotation=25, ha="right")

        ax.grid(True, axis="y", alpha=0.25)

    response = HttpResponse(content_type="image/png")
    fig.tight_layout()
    fig.savefig(response, format="png")
    plt.close(fig)
    return response


def homework_demo_view():
    return