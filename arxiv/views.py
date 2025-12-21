import hashlib
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from urllib.parse import quote
from .forms import ArxivForm
from .models import PdfStorage
from django.db.models import Q
from .models import Arxiv
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def arxiv_create(request):
    if request.method == "POST":
        form = ArxivForm(request.POST, request.FILES)
        if form.is_valid():
            arxiv = form.save(commit=False)

            pdf_file = form.cleaned_data.get("pdf_file")
            if pdf_file:
                data = pdf_file.read()
                sha256 = hashlib.sha256(data).hexdigest()

                pdf_obj, _ = PdfStorage.objects.get_or_create(
                    sha256=sha256,
                    defaults={
                        "file_name": pdf_file.name,
                        "mime_type": "application/pdf",
                        "file_size": pdf_file.size,
                        "content": data,
                        "uploaded_by": request.user,
                    },
                )
                arxiv.pdf = pdf_obj

            arxiv.save()
            return redirect("arxiv_list")
    else:
        form = ArxivForm()

    return render(request, "arxiv/arxiv_form.html", {"form": form})

@login_required
def pdf_view(request, pdf_id):
    pdf = get_object_or_404(PdfStorage, id=pdf_id)

    response = HttpResponse(
        pdf.content,
        content_type=pdf.mime_type or "application/pdf"
    )

    filename = pdf.file_name or "document.pdf"
    response["Content-Disposition"] = (
        f"inline; filename*=UTF-8''{quote(filename)}"
    )
    return response

@staff_member_required
def pdf_delete(request, arxiv_id):
    arxiv = get_object_or_404(Arxiv, id=arxiv_id)

    if not arxiv.pdf:
        messages.warning(request, "PDF файл отсутствует.")
        return redirect("arxiv_list")

    pdf = arxiv.pdf
    arxiv.pdf = None
    arxiv.save()

    pdf.delete()  # удаляем PDF из PdfStorage

    messages.success(request, "PDF файл удалён.")
    return redirect("arxiv_list")

@login_required
def pdf_download(request, pdf_id: int):
    pdf = get_object_or_404(PdfStorage, id=pdf_id)

    # Отдаём PDF с корректным именем (русское имя тоже норм)
    resp = HttpResponse(pdf.content, content_type=pdf.mime_type or "application/pdf")
    filename = pdf.file_name or "document.pdf"
    resp["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"
    return resp

def arxiv_list(request):
    q = request.GET.get("q", "").strip()

    qs = Arxiv.objects.select_related(
        "prog", "region", "district", "object_type", "work_type", "pdf"
    ).all()

    if q:
        qs = qs.filter(
            Q(reg_num__icontains=q) |
            Q(customer__icontains=q) |
            Q(object_name__icontains=q) |
            Q(book_number__icontains=q)
        )

    return render(request, "arxiv/arxiv_list.html", {"items": qs, "q": q})