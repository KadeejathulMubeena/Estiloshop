from django.shortcuts import render, redirect, get_object_or_404
from shop.models import Product, ProductAttribute
from .models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from accounts.forms import AddressForm
from accounts.models import Address
from django.contrib import messages
from orders.models import Coupon,UserCoupons

def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        request.session.create()
        cart_id = request.session.session_key
    return cart_id

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    current_user = request.user
    if current_user.is_authenticated:
        if request.method == 'POST':
            size = request.POST.get('size')
            color = request.POST.get('color')
            attribute = ProductAttribute.objects.filter(product=product, size=size, color=color).first()

        if attribute:
            cart_item, created = CartItem.objects.get_or_create(user=current_user, product_attribute=attribute)
            if not created:
                if cart_item.quantity < attribute.stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    messages.warning(request, f"{product} is already in your cart, and the stock limit has been reached.")
                    return redirect('cart')
            else:
                if cart_item.quantity < attribute.stock:
                    cart_item.quantity = 1  
                    cart_item.save()
                else:
                    messages.warning(request, f"{product} has been added to your cart, but the stock limit has been reached.")

            return redirect('cart')
    else:
        if request.method == 'POST':
            size = request.POST.get('size')
            color = request.POST.get('color')
            attribute = ProductAttribute.objects.filter(product=product, size=size, color=color).first()

            if attribute:
                
                request.session['cart_items_added'] = True
                cart_id = _cart_id(request)
                try:
                    cart = Cart.objects.get(cart_id=cart_id)
                except Cart.DoesNotExist:
                    cart = Cart.objects.create(cart_id=cart_id)
                try:
                    cart_item = CartItem.objects.get(cart=cart, product_attribute=attribute)
                    if cart_item.quantity < attribute.stock:
                        cart_item.quantity += 1
                        cart_item.save()
                    else:
                        messages.warning(request, "You cannot add more items as it exceeds the available stock.")
                except CartItem.DoesNotExist:
                    CartItem.objects.create(product_attribute=attribute, cart=cart, quantity=1)

                return redirect('cart')
    
    return redirect('product_detail', category_slug=product.category.slug, product_slug=product.slug)

def cart(request):
    
    cart = None
    if request.user.is_authenticated:
        cart_items=CartItem.objects.all().filter(user = request.user,is_active=True)
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    # Calculate total, tax, and grand total based on cart items
    total = 0 
    for cart_item in cart_items:
        if cart_item.product_attribute.stock == 0:
            cart_item.delete()
            messages.warning(request, f"{cart_item.product_attribute.product.name} is no longer available and has been removed from your cart.")
            return redirect('cart')

        else:
            if cart_item.product_attribute.offer_price:
                total += cart_item.product_attribute.offer_price * cart_item.quantity
            else:
                total += cart_item.product_attribute.price * cart_item.quantity
            
                
    tax = int((2 * total)//100)
    grand_total = total + tax

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'shop/cart.html', context)


def remove_cart(request, product_attribute_id, cart_item_id):
    product_attribute = get_object_or_404(ProductAttribute, id=product_attribute_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product_attribute = product_attribute, user = request.user, id = cart_item_id)
        else:
            cart_id = _cart_id(request)
            cart = get_object_or_404(Cart, cart_id=cart_id)
            cart_item = CartItem.objects.get(product_attribute = product_attribute, cart = cart, id = cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            if 'applied_coupon' in request.session:
                coupon_id = request.session['applied_coupon']
                coupon = get_object_or_404(Coupon, id=coupon_id)

                if coupon.used_count > 0:
                    coupon.used_count -= 1
                    coupon.save()
                
                used_coupons = UserCoupons.objects.filter(user=request.user, coupon=coupon, is_used=True).first()
                if used_coupons:
                    used_coupons.is_used = False
                    used_coupons.save()

                del request.session['applied_coupon']
            
    except CartItem.DoesNotExist:
        pass
    if 'checkout' in request.META.get('HTTP_REFERER', ''):
        return redirect('checkout')
    else:
        return redirect('cart')

def remove_cart_item(request, product_attribute_id, cart_item_id):
    product_attribute = get_object_or_404(ProductAttribute, id=product_attribute_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product_attribute = product_attribute, user = request.user, id = cart_item_id)
    else:
        cart_id = _cart_id(request)
        cart = get_object_or_404(Cart, cart_id=cart_id)
        cart_item = CartItem.objects.get(product_attribute = product_attribute, cart = cart, id = cart_item_id)
    cart_item.delete()
    if 'applied_coupon' in request.session:
        coupon_id = request.session['applied_coupon']
        coupon = get_object_or_404(Coupon, id=coupon_id)

        if coupon.used_count > 0:
            coupon.used_count -= 1
            coupon.save()
        
        used_coupons = UserCoupons.objects.filter(user=request.user, coupon=coupon, is_used=True).first()
        if used_coupons:
            used_coupons.is_used = False
            used_coupons.save()

        del request.session['applied_coupon']
    if 'checkout' in request.META.get('HTTP_REFERER', ''):
        return redirect('checkout')
    else:
        return redirect('cart')

def increase_quantity(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    if cart_item.quantity + 1 > cart_item.product_attribute.stock:
        messages.warning(request, "You cannot add more items as it exceeds the available stock.")
    else:
        cart_item.quantity += 1
        cart_item.save()

    if 'checkout' in request.META.get('HTTP_REFERER', ''):
        return redirect('checkout')
    else:
        return redirect('cart')


@login_required(login_url='login')
def checkout(request):
    try:
        cart = None
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
   
        total = 0 
        for cart_item in cart_items:
            if cart_item.product_attribute.stock == 0:
                if cart_items.count() == 1:  # Check if it's the only product in the cart
                    cart_item.delete()
                    messages.warning(request,f"{cart_item.product_attribute.product.name} is no longer available and has been removed from your cart.Please add products to proceed with checkout.")
                    return redirect('cart')
                else:
                    cart_item.delete()
                    messages.warning(request, f"{cart_item.product_attribute.product.name} is no longer available and has been removed from your cart.")
            else:
                if cart_item.product_attribute.offer_price:
                    total += cart_item.product_attribute.offer_price * cart_item.quantity
                else:
                    total += cart_item.product_attribute.price * cart_item.quantity
        
        tax = int((2 * total) // 100)
        grand_total = total + tax
        applied_coupon_id = request.session.get('applied_coupon')
        discount = 0
        coupon = None
        if applied_coupon_id and cart_items:
            coupon = Coupon.objects.get(id=applied_coupon_id)
            if total >= coupon.minimum_amount:
                print("total",total)
                print("minimum_amount",coupon.minimum_amount)
                discount = coupon.discount
                grand_total -= discount
            else:
                if coupon.used_count > 0:
                    coupon.used_count -= 1
                    coupon.save()
                
                used_coupons = UserCoupons.objects.filter(user=request.user, coupon=coupon, is_used=True).first()
                if used_coupons:
                    used_coupons.is_used = False
                    used_coupons.save()
                messages.error(request, f'Coupon is removed, Order total should be above {coupon.minimum_amount} to meet the coupon criteria.')

                del request.session['applied_coupon']
    except:
        pass
    addresses = Address.objects.filter(user=request.user)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'addresses': addresses,
        'user': request.user,
        'discount': discount,
        'coupon':coupon 
    }
    return render(request, 'shop/checkout.html', context)
