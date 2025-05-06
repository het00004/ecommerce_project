from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Order, OrderItem, UserProfile , DeliveryInfo , Coupon 
from .models import  Slide 
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.auth import authenticate, login
from .forms import SignUpForm, LoginForm
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import DeliveryInfoForm
from .models import LoginHistory
from django.http import JsonResponse
from .models import Product, Review
from .models import Wishlist, Product


def update_cart(request):
    cart = request.session.get('cart', {})
    for key, value in request.POST.items():
        if key.startswith('quantity_'):
            product_id = key.split('_')[1]
            try:
                quantity = int(value)
                if quantity > 0:
                    cart[product_id] = quantity
                elif quantity == 0:
                    cart.pop(product_id, None)  # remove if quantity is 0
            except ValueError:
                continue

    request.session['cart'] = cart
    return redirect('view_cart')


@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check stock
    if product.stock <= 0:
        messages.error(request, "Product is out of stock.")
        return redirect('product_list')

    # Simulate cart with only this product
    request.session['cart'] = {str(product_id): 1}
    request.session.modified = True

    return redirect('checkout')



@login_required
def profile_view(request):
    profile = request.user.userprofile
    return render(request, 'store/profile.html', {'profile': profile})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            UserProfile.objects.create(user=user)
            return redirect('login')
        
    else:
        form = SignUpForm()
    return render(request, 'store/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Save login history
            LoginHistory.objects.create(user=user)
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.last_login_date = now()
            user_profile.save()

            return redirect('product_list')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'store/login.html')



 # Ensure Slide is imported

def product_list(request):
    # Ensure UserProfile exists for authenticated user
    user_profile = None
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    categories = Category.objects.all()
    slides = Slide.objects.filter(active=True)  # Get only active slides for poster

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'user_profile': user_profile,
        'slides': slides  # 🔥 Pass slides to template
    })





@login_required
def process_payment(request):
    if request.method != 'POST':
        return redirect('product_list')

    # Get the cart from the session
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('product_list')

    total = 0
    order_items = []

    # Calculate total and gather order items
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)

            if product.stock < quantity:
                return render(request, 'store/payment_failed.html', {
                    'message': f"Not enough stock for {product.name}."
                })

            price = product.price * quantity
            total += price
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price,
            })
        except Product.DoesNotExist:
            continue  # Handle case if product doesn't exist

    # Handle coupon logic
    coupon_code = request.POST.get('coupon_code')
    coupon_discount = 0
    total_after_discount = total  # Default if no coupon is used

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if coupon.is_valid():  # Check if coupon is valid
                if request.user in coupon.used_by.all():  # Check if user has already used this coupon
                    messages.error(request, "You have already used this coupon.")
                else:
                    coupon_discount = coupon.discount
                    total_after_discount = max(total - coupon_discount, 0)  # Ensure total does not go negative
                    #coupon.mark_as_used(request.user)  # Mark coupon as used
            else:
                messages.error(request, "This coupon is not valid or has expired.")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")

    # Create the order with discounted total
    order = Order.objects.create(user=request.user, total_price=total_after_discount)

    # Create order items and update stock
    for item in order_items:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            price=item['price']
        )
        item['product'].stock -= item['quantity']  # Update stock after order
        item['product'].save()

    # Extract delivery info from POST
    state = request.POST.get('state')
    city = request.POST.get('city')
    address = request.POST.get('address')
    pin_code = request.POST.get('pin_code')
    phone_number = request.POST.get('phone_number')
    payment_method = request.POST.get('payment_method')

    if not payment_method:
        messages.error(request, "Please select a payment method.")
        return redirect('checkout')

    # Save delivery info
    DeliveryInfo.objects.create(
        user=request.user,
        order=order,
        state=state,
        city=city,
        address=address,
        pin_code=pin_code,
        phone_number=phone_number,
        payment_method=payment_method
    )

    # Clear the cart after payment
    request.session['cart'] = {}

    # Render the payment success page
    return render(request, 'store/payment_success.html', {
        'order': order,
        'coupon': coupon if 'coupon' in locals() else None,
        'discounted_price': total_after_discount
    })



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Default quantity to add is 1
    current_quantity = cart.get(str(product_id), 0)

    # Check if there's enough stock
    if product.stock > current_quantity:
        cart[str(product_id)] = current_quantity + 1  # Update cart
        request.session['cart'] = cart  # Store updated cart in the session

        # Decrease stock
        product.stock -= 1
        product.save()

        messages.success(request, f"Added {product.name} to cart.")
    else:
        messages.error(request, f"Not enough stock for {product.name}.")

    return redirect('product_list')  # Redirect to your product list page after adding to cart



def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    # Loop through the cart items
    for product_id_str, quantity in cart.items():
        product_id = int(product_id_str)  # Ensure product_id is an integer
        product = get_object_or_404(Product, id=product_id)
        price = product.price * quantity
        total += price
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': price
        })

    # Handle upsell and cross-sell logic
    upsell = None
    cross_sells = []

    if cart_items:
        main_product = cart_items[0]['product']  # Use the first product for upsell/cross-sell
        upsell = Product.objects.filter(category=main_product.category).exclude(id=main_product.id).first()
        cross_sells = Product.objects.filter(category=main_product.category).exclude(id=main_product.id)[:3]

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'upsell': upsell,
        'cross_sells': cross_sells,
    })



@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('product_list')

    total = 0
    order_items = []
    upsell = None

    for i, (product_id, quantity) in enumerate(cart.items()):
        product = Product.objects.get(id=product_id)
        price = product.price * quantity
        total += price
        order_items.append({
            'product': product,
            'quantity': quantity,
            'price': product.price,
        })

        # Get the upsell from the first product only
        if i == 0 and product.upsell_product:
            upsell = product.upsell_product

    if request.method == 'POST':
        form = DeliveryInfoForm(request.POST)
        if form.is_valid():
            delivery_info = form.save(commit=False)
            delivery_info.user = request.user
            delivery_info.save()

            order = Order.objects.create(user=request.user, total_price=total)
            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price']
                )

            request.session['cart'] = {}
            return redirect('order_success')
    else:
        form = DeliveryInfoForm()

    return render(request, 'store/checkout.html', {
        'order_items': order_items,
        'total': total,
        'upsell': upsell,
        'form': form
    })



def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        quantity = cart[product_id_str]

        # Restore stock
        product = get_object_or_404(Product, id=product_id)
        product.stock += quantity
        product.save()

        # Remove from cart
        del cart[product_id_str]
        request.session['cart'] = cart

    else:
        messages.error(request, "Product not found in cart.")

    return redirect('view_cart')



@login_required
def generate_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Try to find related delivery info that may include coupon data
    delivery_info = DeliveryInfo.objects.filter(order=order).first()

    # Optional: Recalculate original total from order items
    original_total = sum(item.price * item.quantity for item in order.items.all())
    discounted_total = order.total_price
    discount_amount = original_total - discounted_total

    template_path = 'store/invoice.html'
    context = {
        'order': order,
        'original_total': original_total,
        'discounted_total': discounted_total,
        'discount_amount': discount_amount,
        'coupon_code': delivery_info.coupon.code if delivery_info and hasattr(delivery_info, 'coupon') else None,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return response



@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f"{product.name} added to wishlist.")
    return redirect('product_list')



@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"{product.name} removed from wishlist.")
    return redirect('view_wishlist')



@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})
from .models import Coupon
from.forms import CouponApplyForm
def apply_coupon(request):
    if request.method == 'POST':
        form = CouponApplyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code__iexact=code)
                if coupon.is_valid():
                    request.session['coupon_id'] = coupon.id
                    messages.success(request, f"Coupon '{code}' applied!")
                else:
                    messages.error(request, "Coupon is not valid.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
    return redirect('checkout')



def get_discounted_total(cart_total, request):
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                return cart_total - (cart_total * coupon.discount / 100)
        except Coupon.DoesNotExist:
            pass
    return cart_total

from .models import Slide

def home_view(request):
    slides = Slide.objects.filter(active=True)
    return render(request, 'product_list.html', {'slides': slides})
