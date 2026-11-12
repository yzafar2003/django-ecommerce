from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("store:product_list")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login() cycles the session key but keeps its data, so the cart survives
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("store:product_list")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})
