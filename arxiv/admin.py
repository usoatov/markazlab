from django.contrib import admin
from .models import PdfStorage, Prog, Region, District, ObjectType, WorkType, Arxiv

admin.site.register(PdfStorage)
admin.site.register(Prog)
admin.site.register(Region)
admin.site.register(District)
admin.site.register(ObjectType)
admin.site.register(WorkType)
admin.site.register(Arxiv)
