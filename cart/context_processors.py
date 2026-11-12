from django.conf import settings


def cart(request):
    # just the item count for the header, no db hit
    items = request.session.get(settings.CART_SESSION_KEY, {})
    return {"cart_count": sum(i.get("quantity", 0) for i in items.values())}
