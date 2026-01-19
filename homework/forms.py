from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from homework.models import Classroom

ROLE_CHOICES = (
    ("teacher", "Teacher"),
    ("student", "Student"),
)

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

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    last_name = forms.CharField(label="Фамилия")
    first_name = forms.CharField(label="Имя")
    patronymic  = forms.CharField(label="Отчество", required=False)
    birth_date = forms.DateField(label="Дата рождения", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = User
        fields = (
            "username",
            "role",
            "last_name",
            "first_name",
            "patronymic",
            "birth_date",
            "email",
            "password1",
            "password2",
        )