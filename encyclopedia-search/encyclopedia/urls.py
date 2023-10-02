from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("new", views.new_entry, name="new_entry"),
    path("edit/<str:title>", views.edit, name="edit"),
    path("random", views.random, name="random"),
    path("wiki/<str:title>", views.entry, name="entry")
]
