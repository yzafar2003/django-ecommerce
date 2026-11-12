from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


def make_product(name="Mug", stock=5, price="9.99", available=True, category=None):
    category = category or Category.objects.get_or_create(name="Kitchen", slug="kitchen")[0]
    return Product.objects.create(
        category=category,
        name=name,
        slug=name.lower().replace(" ", "-"),
        price=Decimal(price),
        stock=stock,
        available=available,
    )


class StoreViewTests(TestCase):
    def setUp(self):
        self.mug = make_product("Mug")
        self.hidden = make_product("Hidden Thing", available=False)
        books = Category.objects.create(name="Books", slug="books")
        self.book = make_product("Django Book", category=books)

    def test_list_shows_only_available(self):
        r = self.client.get(reverse("store:product_list"))
        self.assertContains(r, "Mug")
        self.assertContains(r, "Django Book")
        self.assertNotContains(r, "Hidden Thing")

    def test_category_filter(self):
        r = self.client.get(reverse("store:product_list_by_category", args=["books"]))
        self.assertContains(r, "Django Book")
        self.assertNotContains(r, "Mug")

    def test_unknown_category_404(self):
        r = self.client.get(reverse("store:product_list_by_category", args=["nope"]))
        self.assertEqual(r.status_code, 404)

    def test_search(self):
        r = self.client.get(reverse("store:product_list"), {"q": "django"})
        self.assertContains(r, "Django Book")
        self.assertNotContains(r, "<h2>Mug</h2>", html=False)

    def test_detail(self):
        r = self.client.get(self.mug.get_absolute_url())
        self.assertContains(r, "Add to cart")
        self.assertContains(r, "$9.99")

    def test_detail_hidden_product_404(self):
        r = self.client.get(self.hidden.get_absolute_url())
        self.assertEqual(r.status_code, 404)

    def test_out_of_stock_has_no_add_button(self):
        empty = make_product("Empty", stock=0)
        r = self.client.get(empty.get_absolute_url())
        self.assertNotContains(r, "Add to cart")
        self.assertContains(r, "Out of stock")


class SeedCommandTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_store", stdout=StringIO())
        count = Product.objects.count()
        self.assertGreater(count, 0)
        call_command("seed_store", stdout=StringIO())
        self.assertEqual(Product.objects.count(), count)
