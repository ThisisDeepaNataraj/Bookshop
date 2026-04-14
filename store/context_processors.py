def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        from store.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.items.count()
        except:
            count = 0
    else:
        cart_data = request.session.get('cart', {})
        count = sum(item['quantity'] for item in cart_data.values())
    return {'cart_count': count}