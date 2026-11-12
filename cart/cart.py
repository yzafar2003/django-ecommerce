from decimal import Decimal

from django.conf import settings

from store.models import Product


class Cart:
    """Session backed cart.

    Only product ids and quantities live in the session. Prices always come
    from the database so a price change in the admin shows up straight away
    and nobody can tamper with what they pay.
    """

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(settings.CART_SESSION_KEY, {})

    def add(self, product, quantity=1, override=False):
        pid = str(product.id)
        current = 0 if override else self.cart.get(pid, {}).get("quantity", 0)
        quantity = min(current + quantity, product.stock)
        if quantity <= 0:
            self.cart.pop(pid, None)
        else:
            self.cart[pid] = {"quantity": quantity}
        self.save()

    def quantity_of(self, product):
        return self.cart.get(str(product.id), {}).get("quantity", 0)

    def remove(self, product):
        if self.cart.pop(str(product.id), None) is not None:
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.cart = self.session[settings.CART_SESSION_KEY]
        self.save()

    def save(self):
        self.session.modified = True

    def _lines(self):
        products = Product.objects.filter(id__in=self.cart.keys(), available=True)
        by_id = {str(p.id): p for p in products}
        # drop anything that was deleted or switched off since it went in the cart
        stale = [pid for pid in self.cart if pid not in by_id]
        for pid in stale:
            del self.cart[pid]
        if stale:
            self.save()
        for pid, item in self.cart.items():
            product = by_id[pid]
            yield {
                "product": product,
                "quantity": item["quantity"],
                "price": product.price,
                "total": product.price * item["quantity"],
            }

    def __iter__(self):
        return iter(list(self._lines()))

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def total(self):
        return sum((line["total"] for line in self), Decimal("0.00"))
