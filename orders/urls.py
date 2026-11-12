from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("", views.order_history, name="history"),
    path("<int:order_id>/", views.order_detail, name="detail"),
    path("<int:order_id>/cancel/", views.order_cancel, name="cancel"),
]
