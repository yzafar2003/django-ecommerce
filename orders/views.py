from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from cart.cart import Cart

from .forms import CheckoutForm
from .models import Order
from .services import OutOfStock, cancel_order, place_order

# orders placed by a guest in this browser session, so they can see the
# confirmation page without an account
GUEST_ORDERS_KEY = "guest_order_ids"


def _can_view(request, order):
    if request.user.is_authenticated and (order.user_id == request.user.id or request.user.is_staff):
        return True
    return order.id in request.session.get(GUEST_ORDERS_KEY, [])


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("store:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(cart, form, user=request.user)
            except OutOfStock as e:
                messages.error(request, f"{e}. We've updated your cart, please check it and try again.")
                for product in e.products:
                    product.refresh_from_db()
                    cart.add(product, product.stock, override=True)
                return redirect("cart:detail")

            if not request.user.is_authenticated:
                request.session[GUEST_ORDERS_KEY] = request.session.get(GUEST_ORDERS_KEY, []) + [order.id]
            send_mail(
                f"Order #{order.id} received",
                render_to_string("orders/email/confirmation.txt", {"order": order}),
                settings.DEFAULT_FROM_EMAIL,
                [order.email],
                fail_silently=True,
            )
            messages.success(request, "Thanks, your order has been placed.")
            return redirect(order)
    else:
        initial = {}
        if request.user.is_authenticated:
            u = request.user
            initial = {"first_name": u.first_name, "last_name": u.last_name, "email": u.email}
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {"form": form, "lines": list(cart), "cart_total": cart.total()},
    )


def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), id=order_id)
    if not _can_view(request, order):
        raise Http404
    return render(request, "orders/detail.html", {"order": order})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "orders/history.html", {"orders": orders})


@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not _can_view(request, order):
        raise Http404
    if cancel_order(order):
        messages.success(request, f"Order #{order.id} cancelled.")
    else:
        messages.error(request, "Only pending orders can be cancelled.")
    return redirect(order)
