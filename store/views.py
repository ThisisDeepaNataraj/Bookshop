from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Book, Category, Cart, CartItem, Order, OrderItem, UserProfile


def home(request):
    featured_books = Book.objects.filter(featured=True)[:6]
    categories = Category.objects.all()
    latest_books = Book.objects.order_by('-created_at')[:8]
    return render(request, 'store/home.html', {
        'featured_books': featured_books,
        'categories': categories,
        'latest_books': latest_books,
    })


def book_list(request):
    books = Book.objects.all()
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    if category_slug:
        books = books.filter(category__slug=category_slug)
    return render(request, 'store/books.html', {
        'books': books,
        'categories': categories,
        'selected_category': category_slug,
    })


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    related_books = Book.objects.filter(category=book.category).exclude(pk=pk)[:4]
    return render(request, 'store/book_detail.html', {
        'book': book,
        'related_books': related_books,
    })


def search(request):
    query = request.GET.get('q', '')
    books = Book.objects.filter(title__icontains=query) if query else []
    return render(request, 'store/books.html', {
        'books': books,
        'query': query,
        'categories': Category.objects.all(),
    })


@login_required
def cart(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart_obj})


@login_required
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart_obj, book=book)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{book.title}" added to cart.')
    return redirect('cart')


@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def update_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    if not cart_obj.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        order = Order.objects.create(
            user=request.user,
            total_price=cart_obj.get_total(),
            shipping_address=address,
            phone=phone,
        )
        for item in cart_obj.items.all():
            OrderItem.objects.create(
                order=order,
                book=item.book,
                quantity=item.quantity,
                price=item.book.price,
            )
        cart_obj.items.all().delete()
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('orders')

    return render(request, 'store/checkout.html', {'cart': cart_obj})


@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': user_orders})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'store/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    return render(request, 'store/register.html')


def logout_view(request):
    logout(request)
    return redirect('home')