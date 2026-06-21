from django.urls import path
from . import views

urlpatterns = [
    # 🏠 Home and Product Views
    path('', views.home, name='home'),
    path('category/<str:category_name>/', views.category_view, name='category'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # 🛒 Cart and Checkout
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # 👤 Customer Authentication
    path('login/', views.customer_login, name='customer_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # 🧑‍💼 Admin Authentication & Dashboard
    path('admin-login/', views.admin_login, name='admin_login'),
    # ✅ Both routes below will open the same admin dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/', views.admin_dashboard),  # backward-compatible alias

    # 👥 Customer Features
    path('my-orders/', views.my_orders, name='my_orders'),

    # 🛠️ Admin Management Tools (Non-conflicting with Django Admin)
    path('dashboard/add-category/', views.add_category, name='add_category'),
    path('dashboard/add-product/', views.add_product, name='add_product'),
    path('dashboard/sales-report/', views.sales_report, name='sales_report'),

    # ✏️ Edit and 🗑️ Delete Product
    path('dashboard/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('dashboard/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]
