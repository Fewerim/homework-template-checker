from django.contrib import admin
from .models import Profile, Classroom, GradeScale, HomeworkTemplate, StudentSubmission


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role", )


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher")


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ("threshold_2", "threshold_3", "threshold_4", "threshold_5")


@admin.register(HomeworkTemplate)
class HomeworkTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "assigned_date", "deadline")
    list_filter = ("classroom", "deadline")


@admin.register(StudentSubmission)
class StudentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "homework_template", "graded", "grade", "submitted_at")
    list_filter = ("graded", "grade")
