from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import formset_factory

from homework.models import Classroom, HomeworkTemplate


ANSWER_FORMATS = (
    ("text", "Текст"),
    ("int", "Число"),
    ("float", "Дробное"),
)


class ReviewAnswerRowForm(forms.Form):
    number = forms.IntegerField(widget=forms.HiddenInput())
    answer = forms.CharField(label="", required=False)

ReviewAnswerFormSet = formset_factory(ReviewAnswerRowForm, extra=0)


class AnswerRowForm(forms.Form):
    number = forms.IntegerField(widget=forms.HiddenInput())
    answer = forms.CharField(label="", required=False)

AnswerFormSet = formset_factory(AnswerRowForm, extra=0)


class QuestionRowForm(forms.Form):
    number = forms.IntegerField(label="№", min_value=1)
    answer_format = forms.ChoiceField(label="Формат", choices=ANSWER_FORMATS)
    correct_answer = forms.CharField(label="Правильный ответ")

QuestionFormSet = formset_factory(QuestionRowForm, extra=1, can_delete=True)


class DemoHomeworkForm(forms.Form):
    a1 = forms.CharField(label="Ответ 1", required=True)
    a2 = forms.CharField(label="Ответ 2", required=True)
    a3 = forms.CharField(label="Ответ 3", required=True)

    def clean(self):
        cleaned = super().clean()
        for name in ("a1", "a2", "a3"):
            v = (cleaned.get(name) or "").strip()
            match v:
                case _ if len(v) < 2:
                    self.add_error(name, ValidationError("Ответ слишком короткий (минимум 2 символа)."))
                case _ if '.' in v:
                    self.add_error(name, ValidationError("Разделитель в ответе должен быть ','"))
        return cleaned


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    last_name = forms.CharField(label="Фамилия")
    first_name = forms.CharField(label="Имя")
    patronymic = forms.CharField(label="Отчество", required=False)
    birth_date = forms.DateField(label="Дата рождения", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = User
        fields = (
            "username",
            "last_name",
            "first_name",
            "patronymic",
            "birth_date",
            "email",
            "password1",
            "password2",
        )


class SubmissionScoreForm(forms.Form):
    final_score = forms.IntegerField(min_value=0, required=True, label="Итоговые баллы")


class StudentMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        p = getattr(obj, "profile", None)
        last = (getattr(p, "last_name", "") or "").strip()
        first = (getattr(p, "first_name", "") or "").strip()
        patro = (getattr(p, "patronymic", "") or "").strip()
        fio = " ".join(x for x in (last, first, patro) if x)
        if fio:
            return f"{fio} (@{obj.username})"
        return f"@{obj.username}"


class AddStudentsToClassForm(forms.Form):
    students = StudentMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Свободные ученики",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["students"].queryset = User.objects.filter(
            profile__role="student",
            profile__classroom__isnull=True,
        ).order_by("profile__last_name", "profile__first_name")


class ClassroomCreateForm(forms.ModelForm):
    students = StudentMultipleChoiceField(
        queryset=User.objects.filter(profile__role="student", profile__classroom__isnull=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Ученики (свободные)",
    )

    class Meta:
        model = Classroom
        fields = ["name"]


class HomeworkTemplateCreateForm(forms.ModelForm):
    class Meta:
        model = HomeworkTemplate
        fields = (
            "title",
            "description",
            "homework_file",
            "assigned_date",
            "deadline",
            "max_score",
        )
        widgets = {
            "assigned_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
