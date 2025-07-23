from django.contrib import admin
from .models import Product, Seller, UserProfile, Cart, Wishlist, OrderedItem, Order, Review, Payment, CartItem

admin.site.register(Product)
admin.site.register(Seller)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(OrderedItem)
admin.site.register(Order)
admin.site.register(Review)
admin.site.register(Payment)
admin.site.register(CartItem)
