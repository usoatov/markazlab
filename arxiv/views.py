import hashlib
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ArxivForm
from .models import PdfStorage
from django.db.models import Q
from .models import Arxiv

@login_required
def arxiv_create(request):
    if request.method == "POST":
        form = ArxivForm(request.POST, request.FILES)
        if form.is_valid():
            arxiv = form.save(commit=False)

            # Если есть PDF — сохраняем в PdfStorage (BLOB)
            pdf_file = form.cleaned_data.get("pdf_file")
            if pdf_file:
                data = pdf_file.read()
                sha256 = hashlib.sha256(data).hexdigest()

                pdf_obj, created = PdfStorage.objects.get_or_create(
                    sha256=sha256,
                    defaults={
                        "file_name": pdf_file.name,
                        "mime_type": "application/pdf",
                        "file_size": pdf_file.size,
                        "content": data,
                        "uploaded_by": request.user,
                    },
                )
                # Если файл уже был (дубликат по sha256), просто привяжем его
                arxiv.pdf = pdf_obj

            arxiv.save()
            form.save_m2m()
            return redirect("arxiv_list")  # сделаем ниже

    else:
        form = ArxivForm()

    return render(request, "arxiv/arxiv_form.html", {"form": form})

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