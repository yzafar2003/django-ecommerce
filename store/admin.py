from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "available", "updated"]
    list_filter = ["available", "category"]
    list_editable = ["price", "stock", "available"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
