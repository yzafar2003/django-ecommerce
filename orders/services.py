from django.db import transaction
from django.db.models import F

from store.models import Product

from .models import Order, OrderItem


class OutOfStock(Exception):
    def __init__(self, products):
        self.products = products
        names = ", ".join(p.name for p in products)
        super().__init__(f"Not enough stock for: {names}")


def place_order(cart, form, user=None):
    """Turn the cart into an Order.

    Rows are locked with select_for_update so two people buying the last item
    at the same moment can't both get it. Nothing is written unless every
    line has enough stock.
    """
    lines = list(cart)
    if not lines:
        raise ValueError("cart is empty")

    with transaction.atomic():
        ids = [line["product"].id for line in lines]
        locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=ids, available=True)}

        short = [
            line["product"]
            for line in lines
            if line["product"].id not in locked or locked[line["product"].id].stock < line["quantity"]
        ]
        if short:
            raise OutOfStock(short)

        order = form.save(commit=False)
        if user is not None and user.is_authenticated:
            order.user = user
        order.save()

        for line in lines:
            product = locked[line["product"].id]
            OrderItem.objects.create(order=order, product=product, price=product.price, quantity=line["quantity"])
            product.stock -= line["quantity"]
            product.save(update_fields=["stock", "updated"])

    cart.clear()
    return order


def cancel_order(order):
    """Cancel a pending order and put the stock back."""
    with transaction.atomic():
        # re-read under a lock so a double click can't restock twice
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status != Order.Status.PENDING:
            return False
        for item in order.items.all():
            Product.objects.filter(id=item.product_id).update(stock=F("stock") + item.quantity)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated"])
    return True
