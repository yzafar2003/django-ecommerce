from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from store.tests import make_product


class CartTests(TestCase):
    def setUp(self):
        self.mug = make_product("Mug", stock=5, price="10.00")
        self.pen = make_product("Pen", stock=100, price="1.50")

    def add(self, product, quantity, override=False):
        data = {"quantity": quantity}
        if override:
            data["override"] = "True"
        return self.client.post(reverse("cart:add", args=[product.id]), data)

    def cart_page(self):
        return self.client.get(reverse("cart:detail"))

    def test_add_and_total(self):
        self.add(self.mug, 2)
        self.add(self.pen, 4)
        r = self.cart_page()
        self.assertEqual(r.context["cart_total"], Decimal("26.00"))
        self.assertEqual(r.context["cart_count"], 6)

    def test_adding_again_accumulates(self):
        self.add(self.mug, 1)
        self.add(self.mug, 2)
        self.assertEqual(self.cart_page().context["lines"][0]["quantity"], 3)

    def test_override_sets_quantity(self):
        self.add(self.mug, 3)
        self.add(self.mug, 1, override=True)
        self.assertEqual(self.cart_page().context["lines"][0]["quantity"], 1)

    def test_capped_at_stock_with_warning(self):
        r = self.add(self.mug, 50)
        self.assertEqual(self.cart_page().context["lines"][0]["quantity"], 5)
        msgs = [str(m) for m in r.wsgi_request._messages]
        self.assertTrue(any("Only 5" in m for m in msgs))

    def test_invalid_quantity_rejected(self):
        self.add(self.mug, 0)
        self.assertEqual(self.cart_page().context["lines"], [])

    def test_out_of_stock_cannot_be_added(self):
        empty = make_product("Empty", stock=0)
        self.add(empty, 1)
        self.assertEqual(self.cart_page().context["lines"], [])

    def test_get_not_allowed_on_add(self):
        r = self.client.get(reverse("cart:add", args=[self.mug.id]))
        self.assertEqual(r.status_code, 405)

    def test_remove(self):
        self.add(self.mug, 1)
        self.client.post(reverse("cart:remove", args=[self.mug.id]))
        self.assertEqual(self.cart_page().context["lines"], [])

    def test_price_comes_from_database(self):
        self.add(self.mug, 1)
        self.mug.price = Decimal("12.00")
        self.mug.save()
        self.assertEqual(self.cart_page().context["cart_total"], Decimal("12.00"))

    def test_unavailable_product_dropped_from_cart(self):
        self.add(self.mug, 1)
        self.add(self.pen, 1)
        self.mug.available = False
        self.mug.save()
        lines = self.cart_page().context["lines"]
        self.assertEqual([l["product"].name for l in lines], ["Pen"])
