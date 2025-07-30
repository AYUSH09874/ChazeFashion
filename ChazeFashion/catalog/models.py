from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Product Model
class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Boys", "Boys"),
        ("Girls", "Girls"),
        ("Men", "Men"),
        ("Women", "Women"),
        ("Toddler", "Toddler"),
    ]
    SEASON_CHOICES = [
        ("Summer", "Summer"),
        ("Winter", "Winter"),
        ("All Season", "All Season"),
    ]
    pr_id = models.AutoField(primary_key=True)
    pr_cate = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    pr_name = models.CharField(max_length=100)
    pr_price = models.DecimalField(max_digits=10, decimal_places=2)
    pr_reviews = models.FloatField(default=0)
    pr_buy_quant = models.PositiveIntegerField(default=0)
    pr_stk_quant = models.PositiveIntegerField(default=0)
    pr_dimensions = models.CharField(max_length=100, blank=True)
    pr_weights = models.CharField(max_length=50, blank=True)
    pr_offers = models.CharField(max_length=100, blank=True)
    pr_images = models.ImageField(upload_to='product_images/', blank=True, null=True)
    pr_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default="All Season")
    pr_fabric = models.CharField(max_length=50, blank=True)
    pr_texture = models.CharField(max_length=50, blank=True)
    pr_brand = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.pr_name

# Seller Model
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    shop_address = models.TextField()
    contact = models.CharField(max_length=20)

    def __str__(self):
        return self.shop_name

# Cart Model (moved before UserProfile to avoid circular reference)
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalog_cart'

    def __str__(self):
        return f"Cart of {self.user.username}"

# User Profile Extension (removed circular cart reference)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Removed cart field to avoid circular reference - access via user.cart instead

    def __str__(self):
        return self.user.username

# Wishlist Model
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

# CartItem Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

# Ordered Item Model
class OrderedItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

# Order Model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderedItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

# Review Model
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.pr_name}"

# Payment Model
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"


# FIXED SIGNAL HANDLERS
@receiver(post_save, sender=User)
def create_user_profile_and_related_objects(sender, instance, created, **kwargs):
    """
    Create UserProfile, Cart, and Wishlist when a new user is created.
    Uses get_or_create to prevent IntegrityError.
    """
    if created:
        try:
            # Create or get Cart
            cart, cart_created = Cart.objects.get_or_create(user=instance)
            
            # Create or get UserProfile
            user_profile, profile_created = UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'phone': '',
                    'address': '',
                    'wallet_balance': 0,
                }
            )
            
            # Create or get Wishlist
            wishlist, wishlist_created = Wishlist.objects.get_or_create(user=instance)
            
            # Optional: Log creation status (remove in production)
            print(f"User {instance.username} created:")
            print(f"  - Cart: {'created' if cart_created else 'already existed'}")
            print(f"  - Profile: {'created' if profile_created else 'already existed'}")
            print(f"  - Wishlist: {'created' if wishlist_created else 'already existed'}")
            
        except Exception as e:
            print(f"Error creating user-related objects for {instance.username}: {e}")


# Alternative signal handler if you want separate handlers for each model
@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Create Cart for new user"""
    if created:
        Cart.objects.get_or_create(user=instance)

@receiver(post_save, sender=User) 
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile for new user"""
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'phone': '',
                'address': '',
                'wallet_balance': 0,
            }
        )

@receiver(post_save, sender=User)
def create_user_wishlist(sender, instance, created, **kwargs):
    """Create Wishlist for new user"""
    if created:
        Wishlist.objects.get_or_create(user=instance)
