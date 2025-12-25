import hashlib
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from urllib.parse import quote
from .forms import ArxivForm
from .models import PdfStorage
from django.db.models import Q
from .models import Arxiv
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import District
from django.core.paginator import Paginator

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
def arxiv_edit(request, pk: int):
    arxiv = get_object_or_404(Arxiv, pk=pk)

    if request.method == "POST":
        form = ArxivForm(request.POST, request.FILES, instance=arxiv)
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
        form = ArxivForm(instance=arxiv)

    return render(request, "arxiv/arxiv_form.html", {"form": form, "arxiv": arxiv})

@login_required
def arxiv_delete(request, pk: int):
    arxiv = get_object_or_404(Arxiv, pk=pk)

    if request.method != "POST":
        messages.warning(request, "Удаление нужно подтверждать.")
        return redirect("arxiv_list")

    pdf = arxiv.pdf  # запоминаем связанный PDF

    # 1) удаляем запись архива
    arxiv.delete()

    # 2) удаляем PDF из PdfStorage (если есть)
    if pdf:
        try:
            pdf.delete()
        except ProtectedError:
            # Значит этот pdf ещё используется другими записями Arxiv
            messages.warning(
                request,
                "Запись удалена, но PDF не удалён, потому что он привязан к другим документам."
            )
            return redirect("arxiv_list")

    messages.success(request, "Запись и PDF удалены.")
    return redirect("arxiv_list")

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

@login_required
def arxiv_list(request):
    q = request.GET.get("q", "").strip()
    field = request.GET.get("field", "all")  # all | reg_num | customer | object_name | book_number
    page_number = request.GET.get("page", 1)

    qs = Arxiv.objects.all().prefetch_related("prog", "region", "district", "object_type", "pdf").order_by("-id")

    # список разрешённых полей для поиска (чтобы не было “инъекций” через GET)
    allowed_fields = {"all", "reg_num", "customer", "object_name", "book_number"}
    if field not in allowed_fields:
        field = "all"

    if q:
        if field == "all":
            qs = qs.filter(
                Q(reg_num__icontains=q) |
                Q(customer__icontains=q) |
                Q(object_name__icontains=q) |
                Q(book_number__icontains=q)
            )
        else:
            qs = qs.filter(**{f"{field}__icontains": q})

    # можно добавить сортировку
    qs = qs.order_by("-id")

    paginator = Paginator(qs, 10)  # <-- сколько записей на страницу
    page_obj = paginator.get_page(page_number)

    # чтобы при клике Next/Prev сохранялись q и field
    params = request.GET.copy()
    if "page" in params:
        params.pop("page")
    base_qs = params.urlencode()

    return render(request, "arxiv/arxiv_list.html", {
        "page_obj": page_obj,   # пагинация
        "items": page_obj.object_list,  # если в шаблоне уже используется items
        "q": q,
        "field": field,
        "base_qs": base_qs,
    })

@login_required
def districts_by_region(request):
    region_id = request.GET.get("region_id")
    if not region_id:
        return JsonResponse({"results": []})

    qs = District.objects.filter(region_id=region_id).order_by("name")
    data = [{"id": d.id, "name": d.name} for d in qs]
    return JsonResponse({"results": data})