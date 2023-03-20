from django.contrib import admin

# Register your models here.
from .models import Domain, KeywordFile, Product, ProductTemplate

admin.site.register(Domain)
admin.site.register(KeywordFile)
admin.site.register(Product)
admin.site.register(ProductTemplate)
