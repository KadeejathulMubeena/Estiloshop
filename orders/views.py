from django.shortcuts import render, redirect, get_object_or_404
from scarts.models import CartItem
from .forms import OrderForm
from accounts.models import Address
from .models import Order, Payment, OrderProduct,Wallet,WalletTransaction,Coupon,UserCoupons
import datetime
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import transaction
from razorpay import Client
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone




# Create a logger instance
logger = logging.getLogger(__name__)

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')

        if coupon_code:
            coupon = get_object_or_404(Coupon, coupon_code=coupon_code)
            current_user = request.user

            # Check if coupon is already applied to the current order
            if 'applied_coupon' in request.session:
                messages.error(request, 'Coupon has already been applied.')
                return redirect('checkout')

            if coupon.is_used_by_user(current_user):
                messages.error(request, 'Coupon has already been used.')
                return redirect('checkout')

            if not coupon.is_valid():
                messages.error(request, 'Coupon is not valid.')
                return redirect('checkout')

            cart_items = CartItem.objects.filter(user=current_user, is_active=True)
            total = 0
            for cart_item in cart_items:
                if cart_item.product_attribute.stock > 0 :
                    if  cart_item.product_attribute.offer_price:
                        total += cart_item.product_attribute.offer_price * cart_item.quantity
                    else:
                        total += cart_item.product_attribute.price * cart_item.quantity
                 
            if total < coupon.minimum_amount:
                messages.error(request, f'Order total should be above {coupon.minimum_amount} to meet the coupon criteria..')
                return redirect('checkout')

            if coupon.expiration_date < timezone.now().date():
                messages.error(request, 'Coupon has expired.')
                return redirect('checkout')

            if coupon.used_count >= coupon.max_usage:
                messages.error(request, 'Coupon usage limit exceeded.')
                return redirect('checkout')

            request.session['applied_coupon'] = coupon.id 
            coupon.used_count += 1
            coupon.save()
            used_coupons = UserCoupons(user=request.user, coupon=coupon, is_used=True)
            used_coupons.save()
            messages.success(request, 'Coupon applied successfully!')
        else:
            messages.error(request, 'Coupon code cannot be empty.')

    return redirect('checkout')

def remove_coupon(request):
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
        messages.success(request, 'Coupon removed successfully.')
    else:
        messages.error(request, 'No coupon applied to remove.')

    return redirect('checkout')

def payments(request, order_id):
    current_user = request.user
    order = get_object_or_404(Order, id = order_id)
    discount = 0

    if order.coupon:
        discount = order.coupon.discount
    
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop')
    
    tax = 0
    grand_total = 0
    total = 0
    quantity = 0

    for cart_item in cart_items:
        if cart_item.product_attribute.offer_price:
                    price = cart_item.product_attribute.offer_price
        else:
                    price = cart_item.product_attribute.price
        total += (price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = int((2* total) // 100)
    grand_total = total + tax  - discount
    

    try:
        order = Order.objects.get(user=current_user, is_ordered=False, id=order_id)
    except Order.DoesNotExist:
        return redirect('payments', order.id)
    
    context = {
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'discount': discount,
        'grand_total': grand_total,
    }
    return render(request, 'shop/payment.html', context)

def cash_on_delivery(request,order_number):
    current_user = request.user

    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        raise Http404("Order does not exist or is already ordered.") 
    if order.order_total > 1000:
        messages.error(request,'Order above Rs 1000 is not allowed for COD.Please choose another payment method.')
        return redirect('payments', order.id)
    else:
        payment = Payment.objects.create(
                    user=request.user,
                    payment_id=order.order_number,
                    payment_method='COD',
                    amount_paid=0,
                    status='Pending'  
                )

        order.is_ordered = True
        order.payment = payment
        order.updated_at = timezone.now()
        order.save()
               
        cart_items = CartItem.objects.all().filter(user=request.user, is_active=True)

        if cart_items: 
            for cart_item in cart_items:
                product_attribute = cart_item.product_attribute
                if cart_item.product_attribute.offer_price:
                        price = cart_item.product_attribute.offer_price
                else:
                        price = cart_item.product_attribute.price
                order_product = OrderProduct(
                            order=order,
                            payment=payment,
                            user=current_user,
                            product=product_attribute.product,
                            product_attribute=product_attribute,
                            quantity=cart_item.quantity,
                            product_price=price,
                            ordered=True,
                        )
                order_product.save()
                

            cart_items = CartItem.objects.filter(user=request.user, is_active=True).delete()
        mail_subject = "Thank you for your order!"
        message = render_to_string("shop/order_recieved_email.html", {
                            'user': request.user,
                            'order': order
                        })
        to_email = request.user.email
        send_mail(
                            subject=mail_subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[to_email],
                            fail_silently=False,
                        )

        return render(request,'orders/order_success.html',{'order':order})
        
        
@login_required(login_url='login')
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop')
    if all(cart_item.product_attribute.stock <= 0 for cart_item in cart_items):
            messages.error(request, 'All products are out of stock. Please add products in stock.')
            return redirect('checkout')
    grand_total = 0
    tax = 0
    total = 0 
    applied_coupon_id = request.session.get('applied_coupon')

    for cart_item in cart_items:
        if cart_item.product_attribute.stock == 0:
            cart_item.delete()
        if cart_item.product_attribute.offer_price:
                total += cart_item.product_attribute.offer_price * cart_item.quantity
        else:
                total += cart_item.product_attribute.price * cart_item.quantity
            
        quantity += cart_item.quantity
    tax = int((2 * total) // 100)
    grand_total = total + tax
    discount = 0
    coupon = None 
    if applied_coupon_id and cart_items:
        coupon = Coupon.objects.get(id=applied_coupon_id)
        if total >= coupon.minimum_amount:
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
            messages.error(request, f'Coupon is removed, total should be above {coupon.minimum_amount} to meet the coupon criteria.')

            del request.session['applied_coupon']
 

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            selected_address_id = request.POST.get('shipping_address')
            selected_address = get_object_or_404(Address, pk=selected_address_id, user=request.user) 
            data = Order()
            data.user = current_user
            data.shipping_address = selected_address
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.shipping_address = selected_address
            data.save()
            yr = int(datetime.date.today().strftime('%Y'))
            mt = int(datetime.date.today().strftime('%m'))
            dt = int(datetime.date.today().strftime('%d'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.updated_at = timezone.now()
            data.save()
            if applied_coupon_id:
                data.coupon = coupon  
                data.save()
                del request.session['applied_coupon']
            
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'user' : request.user,
                'discount': discount,
                'coupon': coupon ,
            }           
            return render(request, 'shop/payment.html', context)
        else:
            return redirect('checkout')
    else:
        return redirect('checkout')

from django.http import Http404

@transaction.atomic
def confirm_razorpay_payment(request, order_number):
    current_user = request.user
    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        raise Http404("Order does not exist or is already ordered.")    
    total_amount = order.order_total 
    
    # Get the Razorpay payment ID
    razorpay_client = Client(auth=(settings.KEY, settings.SECRET))

        # Create a Razorpay payment
    payment_data = {
            'amount': total_amount * 100,  
            'currency': 'INR',
            'payment_capture': 1  
        }

    razorpay_payment = razorpay_client.order.create(data=payment_data)

        # Get the Razorpay payment ID
    payment_id = razorpay_payment['id']
    payment = Payment.objects.create(
            user=current_user,
            payment_id =payment_id,
            payment_method="Razorpay",
            status="Paid",
            amount_paid=total_amount,
        )
    payment.save()
    order.is_ordered = True
    order.order_number = order_number
    order.payment = payment
    order.updated_at = timezone.now()
    order.save()

    cart_items = CartItem.objects.filter(user=current_user)
    for cart_item in cart_items:
        product_attribute=cart_item.product_attribute
        stock=product_attribute.stock-cart_item.quantity
        product_attribute.stock=stock
        product_attribute.save()
        if cart_item.product_attribute.offer_price:
            price = cart_item.product_attribute.offer_price
        else:
            price = cart_item.product_attribute.price
        order_product = OrderProduct(
                order=order,
                payment=payment,
                user=current_user,
                product=product_attribute.product,
                product_attribute=product_attribute,
                quantity=cart_item.quantity,
                product_price=price,
                ordered=True,
            )
        order_product.save()

    cart_items.delete()
    mail_subject = "Thank you for your order!"
    message = render_to_string("shop/order_recieved_email.html", {
                            'user': request.user,
                            'order': order
                        })
    to_email = request.user.email
    send_mail(
                    subject=mail_subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False,
                        )

    return render(request,'orders/order_success.html',{'order':order})

def failed_payment(request,order_number):
    # Retrieve payment details from Razorpay response

    # Check if the payment ID exists and update its status to 'Failed'
    current_user = request.user
    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        raise Http404("Order does not exist or is already ordered.")    
    total_amount = order.order_total 
    
    # Get the Razorpay payment ID
    razorpay_client = Client(auth=(settings.KEY, settings.SECRET))

        # Create a Razorpay payment
    payment_data = {
            'amount': total_amount * 100,  
            'currency': 'INR',
            'payment_capture': 1  
        }

    razorpay_payment = razorpay_client.order.create(data=payment_data)

        # Get the Razorpay payment ID
    payment_id = razorpay_payment['id']
    payment = Payment.objects.create(
            user=current_user,
            payment_id =payment_id,
            payment_method="Razorpay",
            status="Failed",
            amount_paid=total_amount,
        )
    payment.save()
    order.order_number = order_number
    order.is_ordered = True
    order.payment = payment
    order.updated_at = timezone.now()
    order.save()

    cart_items = CartItem.objects.filter(user=current_user)
    for cart_item in cart_items:
        product_attribute=cart_item.product_attribute
        
        if cart_item.product_attribute.offer_price:
            price = cart_item.product_attribute.offer_price
        else:
            price = cart_item.product_attribute.price
        order_product = OrderProduct(
                order=order,
                payment=payment,
                user=current_user,
                product=product_attribute.product,
                product_attribute=product_attribute,
                quantity=cart_item.quantity,
                product_price=price,
                ordered=True,
            )
        order_product.save()

    cart_items.delete()
    mail_subject = "Payment Failed for Order {}".format(order.order_number)
    message = "Unfortunately, the payment for your order failed. Please try again or contact support."
    send_mail(
        subject=mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[current_user.email],
        fail_silently=False,
    )

    return redirect('my_orders')

def continue_payment(request, order_number):
    current_user = request.user

    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=True)
    except Order.DoesNotExist:
        raise Http404("Order does not exist.")
    # Update payment status to "Paid"
    with transaction.atomic():
        payment = Payment.objects.get(order=order)
        payment.status = "Paid"
        payment.save()

        # Reduce stock for ordered products
        ordered_products = OrderProduct.objects.filter(order=order)
        for ordered_product in ordered_products:
            product_attribute = ordered_product.product_attribute
            product_attribute.stock -= ordered_product.quantity
            product_attribute.save()

        # Update the order's status and save the order
        order.payment = payment
        order.updated_at = timezone.now()
        order.save()

    # Redirect to the order confirmation page
    return redirect('order_confirmed', order_number=order_number)

@transaction.atomic
def payment_with_wallet(request, order_number):
    current_user = request.user

    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        raise Http404("Order does not exist or is already ordered.") 

    try:
        wallet = Wallet.objects.get(user=current_user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=current_user)
        wallet.save()

    if wallet.amount >= order.order_total:
        payment = Payment.objects.create(
            user=request.user,
            payment_id=order.order_number,
            payment_method='Wallet',
            amount_paid=order.order_total,
            status='Pending'  
        )

        order.is_ordered = True
        order.payment = payment
        order.updated_at = timezone.now()
        order.save()

        wallet.amount -= payment.amount_paid
        wallet.save()

        payment.status = 'Paid'
        payment.save()
        WalletTransaction.objects.create(
        wallet=wallet,
        amount=order.order_total,
        transaction_type='Debit'  
        )

        cart_items = CartItem.objects.all().filter(user=request.user, is_active=True)

        if cart_items: 
            for cart_item in cart_items:
                product_attribute = cart_item.product_attribute
                stock = product_attribute.stock - cart_item.quantity
                product_attribute.stock = stock
                product_attribute.save()
                if cart_item.product_attribute.offer_price:
                    price = cart_item.product_attribute.offer_price
                else:
                    price = cart_item.product_attribute.price

                order_product = OrderProduct(
                    order=order,
                    payment=payment,
                    user=current_user,
                    product=product_attribute.product,
                    product_attribute=product_attribute,
                    quantity=cart_item.quantity,
                    product_price=price,
                    ordered=True,
                )
                order_product.save()

            cart_items = CartItem.objects.filter(user=request.user, is_active=True).delete()

        mail_subject = "Thank you for your order!"
        message = render_to_string("shop/order_recieved_email.html", {
                    'user': request.user,
                    'order': order
                })
        to_email = request.user.email
        send_mail(
                    subject=mail_subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False,
                )

        return render(request,'orders/order_success.html',{'order':order})
    else:
        messages.error(request,'Insufficient funds in wallet for this order.') 
        return redirect('payments',order_id = order.id)
        
def order_confirmed(request, order_number):
    user = request.user
    order = Order.objects.get(user = user,order_number=order_number)

    context = {
        'order': order,
    }
    
    return render(request, 'orders/order_success.html',context)

def order_invoice(request, order_id):
    user = request.user
    try:
        order = Order.objects.get(id=order_id)
        ordered_products = OrderProduct.objects.filter(order=order)
        coupon = None 

        if order.coupon:
            try:
                coupon = order.coupon
                coupon_discount = order.coupon.discount
            except Coupon.DoesNotExist:
                coupon = None

        payment = Payment.objects.get(order=order)
        cart_items = CartItem.objects.filter(user=user)

        tax = 0
        grand_total = 0  

        subtotal = 0  
        for order_item in ordered_products:
            total_item = order_item.product_price * order_item.quantity
            order_item.total_item = total_item
            subtotal += total_item

        tax = int((2 * subtotal) // 100)

        grand_total = subtotal + tax  - (coupon_discount if coupon else 0)  

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'grand_total': grand_total,
            'cart_items': cart_items,
            'discount': coupon_discount if coupon else 0,  
            'subtotal': subtotal,
        }

    except Order.DoesNotExist:
        messages.error(request, 'Order does not exist.')  
        return redirect('product_list')  
    return render(request, 'orders/order_invoice.html', context)

 