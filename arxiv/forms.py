from django import forms
from .models import Arxiv, PdfStorage


class ArxivForm(forms.ModelForm):
    # Поле для загрузки PDF (не из модели напрямую)
    pdf_file = forms.FileField(
        required=False,
        help_text="Загрузите PDF (5–10 MB)",
    )

    class Meta:
        model = Arxiv
        fields = [
            "reg_num", "reg_date", "customer",
            "prog", "region", "district",
            "object_type", "object_name",
            "work_type",
            "signed_person", "branch_manager", "specialist",
            "is_mutch", "book_number",
        ]
        widgets = {
            "reg_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_pdf_file(self):
        f = self.cleaned_data.get("pdf_file")
        if not f:
            return f

        # Проверка типа
        if f.content_type not in ("application/pdf",):
            raise forms.ValidationError("Файл должен быть PDF.")

        # Проверка размера (например до 15MB)
        max_mb = 15
        if f.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"PDF не должен быть больше {max_mb} MB.")

        return f
