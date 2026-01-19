from django.urls import path

from . import views
from .views import register_view, profile_view, login_view, logout_view, home_view, homework_demo_view, \
    classroom_detail_view, homework_list_view

urlpatterns = [
    path("", home_view, name="home"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("check_demo/", homework_demo_view, name="check_demo"),
    path("classroom/<int:pk>/", classroom_detail_view, name="classroom_detail"),
    path("homework_list/", homework_list_view, name="homework_list"),
    path("profiles/<int:user_id>/", views.profile_detail, name="profile_detail"),
    path("classrooms/create/", views.classroom_create, name="classroom_create"),
    path("classroom/<int:pk>/add_students/", views.classroom_add_students_view, name="classroom_add_students")
]