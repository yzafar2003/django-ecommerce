from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product

from .cart import Cart
from .forms import AddToCartForm


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Pick a quantity of at least 1.")
        return redirect(product)
    if product.stock == 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect(product)

    cart = Cart(request)
    quantity = form.cleaned_data["quantity"]
    override = form.cleaned_data["override"]
    before = cart.quantity_of(product)
    wanted = quantity if override else before + quantity
    cart.add(product, quantity, override=override)

    if cart.quantity_of(product) < wanted:
        messages.warning(request, f"Only {product.stock} of {product.name} in stock, so your cart has {product.stock}.")
    elif override:
        messages.success(request, f"Updated {product.name}.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect("cart:detail")


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    return redirect("cart:detail")


def cart_detail(request):
    cart = Cart(request)
    lines = list(cart)
    for line in lines:
        line["form"] = AddToCartForm(
            initial={"quantity": line["quantity"], "override": True},
            max_quantity=line["product"].stock,
        )
    return render(request, "cart/detail.html", {"lines": lines, "cart_total": cart.total()})
