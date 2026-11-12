from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.tests import make_product

SIGNUP = {
    "username": "grace",
    "email": "grace@example.com",
    "password1": "a-decent-passphrase-42",
    "password2": "a-decent-passphrase-42",
}


class AccountTests(TestCase):
    def test_signup_logs_in(self):
        r = self.client.post(reverse("signup"), SIGNUP)
        self.assertRedirects(r, reverse("store:product_list"))
        self.assertTrue(User.objects.filter(username="grace").exists())
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    def test_duplicate_email_rejected(self):
        User.objects.create_user("someone", "Grace@Example.com", "x-long-password-1")
        r = self.client.post(reverse("signup"), SIGNUP)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "already exists")

    def test_cart_survives_signup(self):
        mug = make_product("Mug")
        self.client.post(reverse("cart:add", args=[mug.id]), {"quantity": 2})
        self.client.post(reverse("signup"), SIGNUP)
        lines = self.client.get(reverse("cart:detail")).context["lines"]
        self.assertEqual(lines[0]["quantity"], 2)

    def test_login_and_logout(self):
        User.objects.create_user("grace", "grace@example.com", SIGNUP["password1"])
        r = self.client.post(reverse("login"), {"username": "grace", "password": SIGNUP["password1"]})
        self.assertRedirects(r, reverse("store:product_list"))
        r = self.client.post(reverse("logout"))
        self.assertRedirects(r, reverse("store:product_list"))
        self.assertFalse(r.wsgi_request.user.is_authenticated)
