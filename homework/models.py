from django.db import models
from django.contrib.auth.models import User


class Classroom(models.Model):
    name = models.CharField("Имя класса", max_length=64)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="classes_as_teacher",
        verbose_name="Учитель")
    students = models.ManyToManyField(
        User,
        related_name="classes_as_student",
        verbose_name="Ученики",
        blank=True,
    )

    def __str__(self):
        return self.name


class GradeScale(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="grade_scales",
        verbose_name="Учитель",
    )
    threshold_1 = models.PositiveIntegerField("Порог для 1", default=0)
    threshold_2 = models.PositiveIntegerField("Порог для 2", default=30)
    threshold_3 = models.PositiveIntegerField("Порог для 3", default=51)
    threshold_4 = models.PositiveIntegerField("Порог для 4", default=71)
    threshold_5 = models.PositiveIntegerField("Порог для 4", default=89)

    def __str__(self):
        return f'Шкала учителя {self.teacher.username}'


class HomeworkTemplate(models.Model):
    title = models.CharField("Тема задания", max_length=64)
    description = models.TextField("Комментарий к заданию")
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="homeworks",
        verbose_name="Класс",
    )
    homework_file = models.FileField(
        verbose_name="Файл с заданием",
        upload_to="homeworks/",
        blank=True,
        null=True,
    )
    questions = models.JSONField("Структура вопросов")
    correct_answers = models.JSONField("Правильные ответы")
    assigned_date = models.DateField("Дата выдачи")
    deadline = models.DateField("Дедлайн")
    max_score = models.PositiveIntegerField("Максимальный балл", default=0)
    grade_scale = models.ForeignKey(
        GradeScale,
        on_delete=models.PROTECT,
        related_name="homeworks",
        verbose_name="Шкала оценивания",
    )

    def __str__(self):
        return self.title


class StudentSubmission(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Ученик",
    )
    homework_template = models.ForeignKey(
        HomeworkTemplate,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Домашнее задание",
    )
    answers = models.JSONField("Ответы ученика")
    auto_score = models.PositiveIntegerField("Балл после проверки системы", default=0)
    final_score = models.PositiveIntegerField("Итоговый балл", default=0)
    grade = models.PositiveSmallIntegerField("Оценка", null=True, blank=True)
    graded = models.BooleanField("Проверено", default=False)
    teacher_comment = models.TextField("Комментарий учителя", blank=True)
    submitted_at = models.DateTimeField("Время отправки", auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.homework_template.title}"
