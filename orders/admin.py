from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "email", "status", "created"]
    list_filter = ["status", "created"]
    search_fields = ["id", "email", "last_name"]
    inlines = [OrderItemInline]
    actions = ["mark_paid", "mark_shipped"]

    @admin.action(description="Mark selected orders as paid")
    def mark_paid(self, request, queryset):
        queryset.filter(status=Order.Status.PENDING).update(status=Order.Status.PAID)

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        queryset.filter(status=Order.Status.PAID).update(status=Order.Status.SHIPPED)
