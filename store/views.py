from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from cart.forms import AddToCartForm

from .models import Category, Product


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(available=True).select_related("category")

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "store/product_list.html",
        {"category": category, "page": page, "q": q},
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, available=True)
    form = AddToCartForm(max_quantity=product.stock)
    return render(request, "store/product_detail.html", {"product": product, "form": form})
