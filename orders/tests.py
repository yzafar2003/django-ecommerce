from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from store.models import Product
from store.tests import make_product

from .models import Order

ADDRESS = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "address": "12 Analytical St",
    "city": "London",
    "postal_code": "N1 9GU",
}


class CheckoutTests(TestCase):
    def setUp(self):
        self.mug = make_product("Mug", stock=5, price="10.00")
        self.pen = make_product("Pen", stock=10, price="1.50")

    def add(self, product, quantity):
        self.client.post(reverse("cart:add", args=[product.id]), {"quantity": quantity})

    def checkout(self, data=ADDRESS):
        return self.client.post(reverse("orders:checkout"), data)

    def test_empty_cart_redirects(self):
        r = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(r, reverse("store:product_list"))

    def test_guest_checkout_creates_order(self):
        self.add(self.mug, 2)
        self.add(self.pen, 3)
        r = self.checkout()

        order = Order.objects.get()
        self.assertRedirects(r, order.get_absolute_url())
        self.assertIsNone(order.user)
        self.assertEqual(order.total(), Decimal("24.50"))
        self.assertEqual(order.items.count(), 2)

        # stock went down
        self.mug.refresh_from_db()
        self.pen.refresh_from_db()
        self.assertEqual((self.mug.stock, self.pen.stock), (3, 7))

        # cart emptied and confirmation sent
        self.assertEqual(self.client.get(reverse("cart:detail")).context["lines"], [])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Order #{order.id}", mail.outbox[0].subject)
        self.assertIn("Mug", mail.outbox[0].body)

        # guest can see their own confirmation
        self.assertContains(self.client.get(order.get_absolute_url()), "Ada Lovelace")

    def test_order_keeps_price_at_checkout(self):
        self.add(self.mug, 1)
        self.checkout()
        Product.objects.filter(id=self.mug.id).update(price=Decimal("99.00"))
        self.assertEqual(Order.objects.get().total(), Decimal("10.00"))

    def test_invalid_form_does_not_create_order(self):
        self.add(self.mug, 1)
        r = self.checkout({**ADDRESS, "email": "not-an-email"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.mug.refresh_from_db()
        self.assertEqual(self.mug.stock, 5)

    def test_stock_sold_out_meanwhile(self):
        self.add(self.mug, 4)
        self.add(self.pen, 1)
        # someone else bought most of the mugs after we added them
        Product.objects.filter(id=self.mug.id).update(stock=2)

        r = self.checkout()
        self.assertRedirects(r, reverse("cart:detail"))
        self.assertFalse(Order.objects.exists())
        # nothing was decremented, not even the pen
        self.pen.refresh_from_db()
        self.assertEqual(self.pen.stock, 10)
        # cart was trimmed to what's left
        lines = {l["product"].name: l["quantity"] for l in self.client.get(reverse("cart:detail")).context["lines"]}
        self.assertEqual(lines, {"Mug": 2, "Pen": 1})

    def test_logged_in_checkout_links_user_and_prefills(self):
        user = User.objects.create_user("ada", "ada@example.com", "pw-12345-long", first_name="Ada")
        self.client.force_login(user)
        self.add(self.mug, 1)
        r = self.client.get(reverse("orders:checkout"))
        self.assertEqual(r.context["form"].initial["email"], "ada@example.com")
        self.checkout()
        self.assertEqual(Order.objects.get().user, user)
        r = self.client.get(reverse("orders:history"))
        self.assertContains(r, f"#{Order.objects.get().id}")


class OrderAccessTests(TestCase):
    def setUp(self):
        self.mug = make_product("Mug", stock=5, price="10.00")
        self.owner = User.objects.create_user("owner", "o@example.com", "pw-12345-long")
        self.other = User.objects.create_user("other", "x@example.com", "pw-12345-long")
        self.client.force_login(self.owner)
        self.client.post(reverse("cart:add", args=[self.mug.id]), {"quantity": 2})
        self.client.post(reverse("orders:checkout"), ADDRESS)
        self.order = Order.objects.get()

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 404)
        r = self.client.post(reverse("orders:cancel", args=[self.order.id]))
        self.assertEqual(r.status_code, 404)

    def test_anonymous_gets_404(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 404)

    def test_history_requires_login(self):
        self.client.logout()
        r = self.client.get(reverse("orders:history"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)

    def test_staff_can_view(self):
        staff = User.objects.create_user("staff", "s@example.com", "pw-12345-long", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 200)

    def test_cancel_restocks_once(self):
        self.mug.refresh_from_db()
        self.assertEqual(self.mug.stock, 3)
        url = reverse("orders:cancel", args=[self.order.id])
        self.client.post(url)
        self.client.post(url)  # double submit
        self.mug.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.mug.stock, 5)

    def test_cannot_cancel_paid_order(self):
        Order.objects.filter(id=self.order.id).update(status=Order.Status.PAID)
        self.client.post(reverse("orders:cancel", args=[self.order.id]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
