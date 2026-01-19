from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

ROLE_CHOICES = (
    ("teacher", "Teacher"),
    ("student", "Student"),
)

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