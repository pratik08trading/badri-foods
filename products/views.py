from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import Product, Category, CartItem, Order, OrderItem

# ✅ HOME PAGE (Dynamic Product Images)
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()  # show uploaded products on homepage
    return render(request, 'products/index.html', {'categories': categories, 'products': products})


# ✅ CATEGORY VIEW
def category_view(request, category_name):
    category = get_object_or_404(Category, name__iexact=category_name.strip())
    products = category.products.all()
    return render(request, 'products/category.html', {'category': category, 'products': products})


# ✅ PRODUCT DETAIL
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})


# ✅ ADD TO CART
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    cart_item, created = CartItem.objects.get_or_create(
        session_key=session_key,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    total_qty = CartItem.objects.filter(session_key=session_key).aggregate(Sum('quantity'))['quantity__sum'] or 0
    return JsonResponse({'cart_count': total_qty})


# ✅ CART VIEW
def cart_view(request):
    session_key = request.session.session_key
    cart_items = CartItem.objects.filter(session_key=session_key)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'products/cart.html', {'cart_items': cart_items, 'total': total})


# ✅ UPDATE CART QUANTITY
def update_cart_quantity(request, item_id, action):
    item = get_object_or_404(CartItem, id=item_id)

    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
    item.save()

    session_key = item.session_key
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_total = sum(ci.product.price * ci.quantity for ci in cart_items)
    cart_count = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
    item_total = item.product.price * item.quantity

    return JsonResponse({
        'new_quantity': item.quantity,
        'item_total': round(item_total, 2),
        'cart_total': round(cart_total, 2),
        'cart_count': cart_count
    })


# ✅ REMOVE FROM CART
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    session_key = item.session_key
    item.delete()

    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_total = sum(ci.product.price * ci.quantity for ci in cart_items)
    cart_count = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0

    return JsonResponse({
        'cart_total': round(cart_total, 2),
        'cart_count': cart_count
    })


# ✅ CHECKOUT
def checkout(request):
    session_key = request.session.session_key
    cart_items = CartItem.objects.filter(session_key=session_key)

    if not cart_items.exists():
        return render(request, 'products/checkout.html', {'order_items': [], 'total': 0})

    total = sum(item.product.price * item.quantity for item in cart_items)
    user = request.user if request.user.is_authenticated else None

    order = Order.objects.create(user=user, session_key=session_key, total=total)

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    order_items = list(cart_items)
    cart_items.delete()
    request.session.modified = True

    return render(request, 'products/checkout.html', {
        'order_items': order_items,
        'total': total
    })


# ✅ CUSTOMER LOGIN
def customer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and not user.is_staff:
            login(request, user)
            return redirect('home')
        elif user and user.is_staff:
            messages.error(request, "Please use the admin login page.")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'products/customer_login.html')


# ✅ ADMIN LOGIN
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid admin credentials.")
    return render(request, 'products/admin_login.html')


# ✅ LOGOUT
def logout_view(request):
    logout(request)
    return redirect('customer_login')


# ✅ REGISTER
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username already exists.')
    return render(request, 'products/register.html')


# ✅ MY ORDERS
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/my_orders.html', {'orders': orders})


# ✅ ADMIN DASHBOARD (Enhanced)
@staff_member_required
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
    total_products = Product.objects.count()

    top_categories = (
        OrderItem.objects
        .values('product__category__name')
        .annotate(
            total_sales=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        )
        .order_by('-total_sales')[:5]
    )

    top_products = (
        OrderItem.objects
        .values('product__name')
        .annotate(total_sales=Sum('quantity'))
        .order_by('-total_sales')[:10]
    )

    recent_orders = Order.objects.order_by('-created_at')[:10]
    all_products = Product.objects.select_related('category').all()

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'top_categories': top_categories,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'all_products': all_products,
    }

    return render(request, 'products/admin_dashboard.html', context)


# ✅ ADD CATEGORY
@staff_member_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category already exists!")
        else:
            Category.objects.create(name=name, description=description)
            messages.success(request, f"Category '{name}' added successfully!")
            return redirect('admin_dashboard')

    return render(request, 'products/add_category.html')


# ✅ ADD PRODUCT
@staff_member_required
def add_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        category = get_object_or_404(Category, id=category_id)
        product = Product(name=name, description=description, price=price, category=category)

        if image:
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            product.image = filename

        product.save()
        messages.success(request, f"Product '{name}' added successfully!")
        return redirect('admin_dashboard')

    return render(request, 'products/add_product.html', {'categories': categories})


# ✅ EDIT PRODUCT
@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        category_id = request.POST.get('category')

        if category_id:
            product.category = get_object_or_404(Category, id=category_id)

        image = request.FILES.get('image')
        if image:
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            product.image = filename

        product.save()
        messages.success(request, f"✅ Product '{product.name}' updated successfully!")
        return redirect('admin_dashboard')

    return render(request, 'products/edit_product.html', {'product': product, 'categories': categories})


# ✅ DELETE PRODUCT
@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f"🗑️ Product '{product_name}' deleted successfully.")
    return redirect('admin_dashboard')


# ✅ SALES REPORT (Improved)
@staff_member_required
def sales_report(request):
    category_sales = (
        OrderItem.objects
        .values('product__category__name')
        .annotate(
            total_sales=Sum('quantity'),
            total_revenue=Sum(ExpressionWrapper(F('price') * F('quantity'),
                                                output_field=DecimalField(max_digits=12, decimal_places=2)))
        )
        .order_by('-total_revenue')
    )

    product_sales = (
        OrderItem.objects
        .values('product__name')
        .annotate(
            total_sales=Sum('quantity'),
            total_revenue=Sum(ExpressionWrapper(F('price') * F('quantity'),
                                                output_field=DecimalField(max_digits=12, decimal_places=2)))
        )
        .order_by('-total_revenue')[:10]
    )

    return render(request, 'products/sales_report.html', {
        'category_sales': category_sales,
        'product_sales': product_sales,
    })
