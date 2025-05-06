from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import signup_view
from .views import profile_view


urlpatterns = [
    path('product_list/', views.product_list, name='product_list'),
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('invoice/<int:order_id>/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('signup/', signup_view, name='signup'),
    path('', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),
    path('profile/', profile_view, name='profile'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
  


]
