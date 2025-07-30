from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, UserProfile, Cart, Wishlist, Order, CartItem
from .forms import UserProfileForm

def home(request):
    """Home/Landing page"""
    products = Product.objects.all()[:8]  # Show first 8 products
    context = {
        'products': products,
    }
    return render(request, 'catalog/home.html', context)

def signup(request):
    """User registration - FIXED VERSION"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user - signal handlers will automatically create UserProfile, Cart, and Wishlist
                user = form.save()
                
                # Login the user immediately
                login(request, user)
                messages.success(request, f'Welcome to ChazeFashion, {user.username}! Your account has been created successfully.')
                return redirect('home')
                
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}. Please try again.')
                return render(request, 'catalog/signup.html', {'form': form})
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = UserCreationForm()
    
    return render(request, 'catalog/signup.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'catalog/login.html')

@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    """User profile page - FIXED VERSION"""
    # Use get_or_create to handle cases where profile might not exist
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'catalog/profile.html', context)

def product_list(request):
    """Product catalog with filtering"""
    products = Product.objects.all()
    
    # Filtering
    category = request.GET.get('category')
    season = request.GET.get('season')
    fabric = request.GET.get('fabric')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    brand = request.GET.get('brand')
    
    if category:
        products = products.filter(pr_cate=category)
    if season:
        products = products.filter(pr_season=season)
    if fabric:
        products = products.filter(pr_fabric__icontains=fabric)
    if price_min:
        try:
            products = products.filter(pr_price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(pr_price__lte=float(price_max))
        except ValueError:
            pass
    if brand:
        products = products.filter(pr_brand__icontains=brand)
    
    context = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'seasons': Product.SEASON_CHOICES,
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page"""
    product = get_object_or_404(Product, pr_id=product_id)
    reviews = product.review_set.all().order_by('-created_at')
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'catalog/product_detail.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add product to cart (with quantity) - ENHANCED VERSION"""
    product = get_object_or_404(Product, pr_id=product_id)
    
    # Ensure cart exists (signal should create it, but just in case)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get quantity from POST data
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f'Updated {product.pr_name} quantity in cart!')
    else:
        messages.success(request, f'{product.pr_name} added to cart!')
    
    return redirect('cart')

@login_required
def cart(request):
    """View cart and update quantities - ENHANCED VERSION"""
    # Ensure cart exists
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    if request.method == 'POST':
        try:
            for item in cart_items:
                qty_key = f'quantity_{item.id}'
                qty = int(request.POST.get(qty_key, item.quantity))
                
                if qty > 0:
                    item.quantity = qty
                    item.save()
                else:
                    item.delete()
            
            messages.success(request, 'Cart updated successfully!')
            return redirect('cart')
            
        except (ValueError, TypeError) as e:
            messages.error(request, 'Invalid quantity values. Please enter valid numbers.')
    
    # Calculate total
    total = sum(item.product.pr_price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'catalog/cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.pr_name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart.')
    except Exception as e:
        messages.error(request, 'Error removing item from cart.')
    
    return redirect('cart')

@login_required
def wishlist(request):
    """User wishlist - FIXED VERSION"""
    # Ensure wishlist exists (signal should create it, but just in case)
    user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    context = {
        'wishlist': user_wishlist,
    }
    return render(request, 'catalog/wishlist.html', context)

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist - IMPROVED VERSION"""
    product = get_object_or_404(Product, pr_id=product_id)
    
    # Ensure wishlist exists
    user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Check if product is already in wishlist
    if user_wishlist.products.filter(pr_id=product_id).exists():
        messages.info(request, f'{product.pr_name} is already in your wishlist!')
    else:
        user_wishlist.products.add(product)
        messages.success(request, f'{product.pr_name} added to wishlist!')
    
    return redirect('product_detail', product_id=product_id)

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist - IMPROVED VERSION"""
    try:
        product = get_object_or_404(Product, pr_id=product_id)
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        if user_wishlist.products.filter(pr_id=product_id).exists():
            user_wishlist.products.remove(product)
            messages.success(request, f'{product.pr_name} removed from wishlist.')
        else:
            messages.info(request, 'Product was not in your wishlist.')
            
    except Exception as e:
        messages.error(request, 'Error removing product from wishlist.')
    
    return redirect('wishlist')
