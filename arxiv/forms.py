from django import forms
from .models import Arxiv, PdfStorage


class ArxivForm(forms.ModelForm):
    pdf_file = forms.FileField(required=False, label="PDF файл")

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
        widgets = {"reg_date": forms.DateInput(attrs={"type": "date"})}

    def clean_pdf_file(self):
        f = self.cleaned_data.get("pdf_file")
        if not f:
            return f
        if f.content_type not in ("application/pdf",):
            raise forms.ValidationError("Только PDF файл.")
        if f.size > 15 * 1024 * 1024:
            raise forms.ValidationError("PDF не должен быть больше 15 MB.")
        return f