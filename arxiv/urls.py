from django.urls import path
from . import views

urlpatterns = [
    path("", views.arxiv_list, name="arxiv_list"),
    path("create/", views.arxiv_create, name="arxiv_create"),
]
