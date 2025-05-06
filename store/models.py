from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)


    def __str__(self):
        return self.name
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    last_login_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Automatically set the username from the associated user model before saving
        self.username = self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/multiple/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)
    upsell_product = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='upsells'
    )
    cross_sells = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='cross_sold_with'
    )

    def __str__(self):
        return self.name 
class ProductImage(models.Model):
    product = models.ForeignKey('Product', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/multiple/')
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.product.name} - Image"


   
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')

    def __str__(self):
        return f"Order {self.id} for {self.user.username}"

# OrderItem model with price at the time of purchase
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Item {self.product.name} in Order {self.order.id}"
    
# delivery info #
class DeliveryInfo(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # Assuming you have a user model
    order = models.OneToOneField('Order', on_delete=models.CASCADE, null=True, blank=True)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    pin_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=50 ,default='upi')
    
    def __str__(self):
        return f"{self.user.username} -{self.payment_method} , {self.city}, {self.state} ,{self.address}, {self.phone_number}"


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"

class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Review on {self.product.name}"
    

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.ManyToManyField(User, blank=True, related_name='used_coupons')

    def is_valid(self):
        return self.expiry_date > timezone.now()

    def __str__(self):
        return self.code
    
class Slide(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='poster_slides/')
    link = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title