from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product

CATALOG = {
    "Electronics": [
        ("Wireless Headphones", "Over-ear, 30 hour battery, active noise cancelling.", "89.99", 25),
        ("Mechanical Keyboard", "Hot-swappable switches, aluminium case.", "119.00", 12),
        ("USB-C Charger 65W", "GaN charger, two USB-C ports and one USB-A.", "39.50", 40),
        ("Smart Watch", "Heart rate, GPS, a week of battery.", "149.00", 8),
    ],
    "Clothing": [
        ("Cotton T-Shirt", "Heavyweight organic cotton, regular fit.", "18.00", 100),
        ("Denim Jacket", "Classic trucker jacket in mid-wash denim.", "65.00", 15),
        ("Running Shoes", "Lightweight trainers with a cushioned sole.", "79.99", 20),
    ],
    "Home & Kitchen": [
        ("Pour-Over Coffee Set", "Glass dripper, carafe and 100 filters.", "34.00", 30),
        ("Cast Iron Skillet", "Pre-seasoned 10 inch skillet.", "29.99", 18),
        ("Linen Throw Blanket", "Stonewashed linen, 130 x 170 cm.", "49.00", 0),
    ],
    "Books": [
        ("Two Scoops of Django", "Best practices for Django projects.", "44.95", 10),
        ("Fluent Python", "Clear, concise and effective programming.", "55.00", 7),
    ],
}


class Command(BaseCommand):
    help = "Fill the store with some demo categories and products (safe to run more than once)."

    def handle(self, *args, **options):
        created = 0
        for cat_name, products in CATALOG.items():
            category, _ = Category.objects.get_or_create(slug=slugify(cat_name), defaults={"name": cat_name})
            for name, description, price, stock in products:
                _, was_created = Product.objects.get_or_create(
                    slug=slugify(name),
                    defaults={
                        "category": category,
                        "name": name,
                        "description": description,
                        "price": Decimal(price),
                        "stock": stock,
                    },
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new products ({Product.objects.count()} total)."))
