from django.urls import path
from . import views

urlpatterns = [
    path("", views.arxiv_list, name="arxiv_list"),
    path("create/", views.arxiv_create, name="arxiv_create"),
    path("pdf/<int:pdf_id>/view/", views.pdf_view, name="pdf_view"),
    path("pdf/<int:pdf_id>/download/", views.pdf_download, name="pdf_download"),
    path("pdf/delete/<int:arxiv_id>/", views.pdf_delete, name="pdf_delete"),
]
