from django.conf import settings
from django.db import models


# --- PDF storage (отдельная таблица, вариант B: LONGBLOB) ---
class PdfStorage(models.Model):
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, default="application/pdf")
    file_size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, unique=True, null=True, blank=True)
    content = models.BinaryField()  # MySQL -> LONGBLOB
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="pdf_files",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pdf_storage"

    def __str__(self):
        return self.file_name


# --- Справочники ---
class Prog(models.Model):
    prog_name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "prog"
        ordering = ["prog_name"]

    def __str__(self):
        return self.prog_name


class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "region"
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # Если районы привязаны к области, лучше так:
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="districts",
        null=True, blank=True
    )

    class Meta:
        db_table = "district"
        ordering = ["name"]
        indexes = [models.Index(fields=["region", "name"])]

    def __str__(self):
        return self.name


class ObjectType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "object_type"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkType(models.Model):
    name = models.CharField(max_length=255, unique=True)



# --- Основная таблица архива ---
class Arxiv(models.Model):
    reg_num = models.CharField("Ro`yxatga olingan raqami", max_length=100, unique=True)       # регистрационный номер
    reg_date = models.DateField('Sana')                                  # дата регистрации
    customer = models.CharField('Buyurtmachi', max_length=255)                    # заказчик

    prog = models.ForeignKey(
        Prog,
        verbose_name="Dastur nomi",
        on_delete=models.PROTECT,
        related_name="arxiv_items"
    )

    region = models.ForeignKey(
        Region,
        verbose_name="Viloyat",
        on_delete=models.PROTECT,
        related_name="arxiv_items"
    )

    district = models.ForeignKey(
        District, 
        verbose_name="Tuman",
        on_delete=models.PROTECT, 
        related_name="arxiv_items"
    )
    
    

    object_type = models.ForeignKey(ObjectType, verbose_name="Obyekt turi", on_delete=models.PROTECT, related_name="arxiv_items")
    object_name = models.CharField('Ob`yekt nomi', max_length=255)                 # наименование объекта

    work_type = models.CharField("Ish turi", max_length=255)

    signed_person = models.CharField('Bayonnomani imzolagan shaxs', max_length=255)               # подписавший человек
    branch_manager = models.CharField('Filial rahbari', max_length=255)              # руководитель филиала
    specialist = models.CharField('Sinov o`tkazgan mutaxassis', max_length=255)                  # специалист

    is_mutch = models.BooleanField('Muvofiq', default=False)                  # boolean
    book_number = models.CharField('Kitob raqami', max_length=100, blank=True)     # номер книги архива

    pdf = models.ForeignKey(
        PdfStorage,
        on_delete=models.PROTECT,   # нельзя удалить PDF, если привязан
        related_name="arxiv_items",
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "arxiv"
        ordering = ["-reg_date", "-id"]
        indexes = [
            models.Index(fields=["reg_num"]),
            models.Index(fields=["reg_date"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["region", "district"]),
        ]

    def __str__(self):
        return f"{self.reg_num} ({self.reg_date})"
