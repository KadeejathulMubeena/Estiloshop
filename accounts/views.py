from django.shortcuts import render, redirect,get_object_or_404
from .forms import RegistrationForm, UserProfileForm, UserForm,AddressForm
from .models import Account,UserProfile,Address,State,District
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from scarts.models import Cart, CartItem
from scarts.views import _cart_id
from orders.models import Order,Payment,OrderProduct,Wallet,WalletTransaction
from orders.forms import CancellationReasonForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            existing_blocked_user = Account.objects.filter(email=email, is_blocked=True).first()

            if existing_blocked_user:
                messages.error(request, 'Account with this email is blocked.')
            elif first_name.strip()=="":
                messages.error(request, 'First name cannot be empty or contain only spaces.')
            elif first_name.strip() and len(first_name) < 3:
                messages.error(request, 'First name should have atleast 3 letters.')
            elif len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            elif not any(char.isupper() for char in password):
                messages.error(request, 'Password must contain at least one uppercase letter.')
            elif not any(char.islower() for char in password):
                messages.error(request, 'Password must contain at least one lowercase letter.')
            elif not any(char.isdigit() for char in password):
                messages.error(request, 'Password must contain at least one digit.')
            elif not any(char in r'!@#$%^&*()-_=+[{]}\|;:,<.>/?' for char in password):
                messages.error(request, 'Password must contain at least one special character.')
            else:
                # Validate against common patterns and words
                common_patterns = ['password', '12345678', 'abcdefghi','abcd1234', 'admin']
                if any(pattern in password.lower() for pattern in common_patterns):
                    messages.error(request, 'Password must not contain common patterns or easily guessable passwords.')
                else:
                    user = Account.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                    user.save()

                    current_site = get_current_site(request)
                    mail_subject = "Please activate your account"
                    message = render_to_string("accounts/account_verification_email.html", {
                        'user': user,
                        'domain': current_site,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                    })
                    to_email = email
                    send_mail(
                        subject=mail_subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[to_email],
                        fail_silently=False,
                    )

                    return redirect('/accounts/login/?command=verification&email=' + email)
        else:
            messages.error(request, 'Form validation failed. Please check the input.')

    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def log_in(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user:
            if not user.is_active:
                messages.error(request, 'Your account is not activated.')
                return redirect('login')  
            
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)
                    for item in cart_items:
                        existing_item = CartItem.objects.filter(user=user, product_attribute=item.product_attribute).first()
                        if existing_item:
                            remaining_quantity = item.quantity
                            while remaining_quantity > 0:
                                if existing_item.quantity < item.product_attribute.stock:
                                    existing_item.quantity += 1
                                    existing_item.save()
                                    remaining_quantity -= 1
                                else:
                                    messages.warning(request, f"Adding {item.product_attribute.product} to your cart exceeds the available stock.")
                                    break
                            item.delete()  
                        else:
                            if item.quantity <= item.product_attribute.stock:
                                item.user = user
                                item.save()
                            else:
                                messages.warning(request, f"Adding {item.product_attribute.product} to your cart exceeds the available stock.")
            except Cart.DoesNotExist:
                pass

            if not user.is_blocked and user.is_authenticated:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_home') 
                else:
                    if 'cart_items_added' in request.session:
                        del request.session['cart_items_added']
                        return redirect('cart')
                    else:
                        return redirect('home') 
            else:
                messages.error(request, 'Account with this email is blocked.')
        else:
            messages.error(request, 'Invalid login credentials')
    
    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def log_out(request):
    logout(request)
    messages.success(request,"You are Logged out.")
    return redirect('login')

def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except (ValueError,TypeError,OverflowError,Account.DoesNotExist):
        user=None

    if user and default_token_generator.check_token(user, token):
        user.is_active=True
        user.save()
        messages.success(request,"Congratulations! Your account is activated. ")
        return redirect('login')
    else:
        messages.error(request,"Invalid activation link")
        return redirect('register')
  
def forgotpassword(request):   
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = get_object_or_404(Account, email__iexact=email)
                current_site = get_current_site(request)
                mail_subject = "Reset your Password"
                message = render_to_string("accounts/resetpassword_validation.html",{
                    'user':user,
                    'domain':current_site,
                    'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                    'token':default_token_generator.make_token(user),
                })
                to_email = email
                send_mail(
                    subject=mail_subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL, 
                    recipient_list=[to_email],
                    fail_silently=False,  
                )
                messages.success(request,'Password reset email has been sent to your email')
                return redirect('login')
            except ObjectDoesNotExist:
                messages.error(request,'Account does not exist.')
                return redirect('forgotpassword')
        else:
            messages.error(request, 'Email is required for password reset.')
            return redirect('forgotpassword')

    return render(request,'accounts/forgotpassword.html')

def resetpassword_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except (ValueError,TypeError,OverflowError,Account.DoesNotExist):
        user=None

    if user and default_token_generator.check_token(user, token):
        request.session['uid']=uid
        messages.success(request,'Please reset your Password')
        return redirect('resetpassword')
    else:
        messages.error(request,'This link has been expired')
        return redirect('login')

    
def resetpassword(request):
    if request.method=='POST':
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']
        if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
        elif not any(char.isupper() for char in password):
                messages.error(request, 'Password must contain at least one uppercase letter.')
        elif not any(char.islower() for char in password):
                messages.error(request, 'Password must contain at least one lowercase letter.')
        elif not any(char.isdigit() for char in password):
                messages.error(request, 'Password must contain at least one digit.')
        elif not any(char in r'!@#$%^&*()-_=+[{]}\|;:,<.>/?' for char in password):
                messages.error(request, 'Password must contain at least one special character.')
        else:
            if password == confirm_password:
                uid=request.session.get('uid')
                user=Account.objects.get(pk=uid)
                user.set_password(password)
                user.save()
                messages.success(request,'Password reset successful.')
                return redirect('login')
            else:
                messages.error(request,'Password doest not match')
                return redirect('resetpassword')

    return render(request,'accounts/resetpassword.html')

@login_required(login_url='login')
def dashboard(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        userprofile = None
    orders = Order.objects.order_by('-created_at').filter(user_id = request.user.id,is_ordered = True)
    orders_count = orders.count()

    context = {
        'orders' : orders,
        'orders_count' : orders_count,
        'userprofile' :userprofile,
    }
    return render(request, 'accounts/dashboard.html',context)

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.order_by('-created_at').filter(user_id = request.user.id,is_ordered = True)
    context = {
        'orders' : orders,
    }
    return render(request, 'accounts/my_order.html', context)

@login_required(login_url='login')
def edit_profile(request):
    order = Order.objects.filter(user=request.user, is_ordered=True).first() 
    userprofile = UserProfile.objects.get_or_create(user=request.user)[0]  

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            phone = request.POST['phone']
            first_name = user_form.cleaned_data['first_name']
            if first_name.strip()=="":
                messages.error(request, 'First name cannot be empty or contain only spaces.')
            elif first_name.strip() and len(first_name) < 3:
                messages.error(request, 'First name should have atleast 3 letters.')
            else:
                if phone.isdigit() and len(phone) == 10 and not phone.startswith(('0', '1', '2', '3', '4', '5')):            
                    user_form.save()
                    profile_form.save()
                    messages.success(request, 'Your Profile has been updated')
                    return redirect('edit_profile')
                else:
                    messages.error(request, 'Invalid phone number')

        else:
            if 'profile_picture' in profile_form.errors:
                messages.error(request,'Choose valid image file!')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact = request.user.username)
        if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
        elif not any(char.isupper() for char in new_password):
                messages.error(request, 'Password must contain at least one uppercase letter.')
        elif not any(char.islower() for char in new_password):
                messages.error(request, 'Password must contain at least one lowercase letter.')
        elif not any(char.isdigit() for char in new_password):
                messages.error(request, 'Password must contain at least one digit.')
        elif not any(char in r'!@#$%^&*()-_=+[{]}\|;:,<.>/?' for char in new_password):
                messages.error(request, 'Password must contain at least one special character.')
        else:
            if new_password == confirm_password:
                success = user.check_password(current_password)
                if success:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password Updated Successfully')
                    return redirect('change_password')
                else:
                    messages.error(request, 'Please Enter Valid Password')
                    return redirect('change_password')
            else:
                messages.error(request, 'Password does not match !')
                return redirect('change_password')
        
    return render(request, 'accounts/change_password.html')

@login_required(login_url='login')
def order_detail(request,order_id):

    order_detail = OrderProduct.objects.filter(order__order_number=order_id) 
    order = get_object_or_404(Order, order_number=order_id)
    payment = get_object_or_404(Payment, id=order.payment.id)
    if order.status == 'Delivered':
        payment.status = 'Paid'
        payment.save()
    coupon_discount = 0
    if order.coupon:
        coupon_discount = order.coupon.discount
           
    total = 0
    subtotal = 0
    for i in order_detail:
        total =i.product_price * i.quantity
        subtotal += i.product_price * i.quantity
        i.total = total
    grand_total = order.order_total
    context = {
        'order': order,
        'order_detail': order_detail,
        'subtotal':subtotal,
        'payment' : payment,
        'coupon_discount':coupon_discount ,
        'grand_total':grand_total
        
    }
    return render(request, 'accounts/order_detail.html',context)

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    form = CancellationReasonForm() 

    if request.method == 'POST':
        form = CancellationReasonForm(request.POST)  
        if form.is_valid():
            cancellation_reason = form.cleaned_data['cancellation_reason'] 
            order.status = 'Cancelled'
            order.cancellation_reason = cancellation_reason  
            order.save()
            cancelled_attributes = order.orderproduct_set.all()
            
            if order.payment.status == 'Paid':
                wallet = Wallet.objects.get(user = request.user)
                wallet.amount += order.payment.amount_paid
                wallet.save()
                WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=order.payment.amount_paid,
                        transaction_type='Credit'
                    )
                order.payment.amount_paid = 0
                order.payment.status = ''
                order.payment.save()
                for cancelled_attr in cancelled_attributes:
                    product_attr = cancelled_attr.product_attribute

                    product_attr.stock += cancelled_attr.quantity
                    product_attr.save()
            elif order.payment.status == 'Pending':
                order.payment.amount_paid = 0
                order.payment.status = ''
                order.payment.save()

            return redirect('my_orders')
    return render(request, 'accounts/cancel_order_confirmation.html', {'order': order,'form': form})

def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    payment = get_object_or_404(Payment, id=order.payment.id)

    if request.method == 'POST':
        return_reason = request.POST['return_reason']
        order.status = 'Returned'
        order.return_reason = return_reason
        order.save()
        order.payment.amount_paid = 0
        order.payment.status = ''
        order.payment.save()
        returned_attributes = order.orderproduct_set.all()
        for returned_attr in returned_attributes:
            product_attr = returned_attr.product_attribute
            product_attr.stock += returned_attr.quantity
            product_attr.save()

        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet.amount += payment.amount_paid
            wallet.save()
            
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(
                user=request.user,
                amount=payment.amount_paid,
            )
        if wallet:
            WalletTransaction.objects.create(
            wallet=wallet,
            amount=payment.amount_paid,
            transaction_type='Credit' 
            )
   
        messages.success(request, "Order returned successfully.")
        return redirect('my_orders')
    
    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'accounts/return_order_confirmation.html', context)


def add_address(request):
    states = State.objects.all()
    if request.method == 'POST':
        print(request.POST)
        form = AddressForm(request.POST)
        if form.is_valid():
            address = Address()
            address.address_line_1 = form.cleaned_data['address_line_1']
            address.address_line_2 = form.cleaned_data['address_line_2']
            address.country = form.cleaned_data['country']
            address.state = form.cleaned_data['state']
            address.district = form.cleaned_data['district']
            address.postal_code = form.cleaned_data['postal_code']
            address.user = request.user
            address.save()
            return redirect('place_order')
    else:
        form = AddressForm()

    context = {
        'form':form,
        'states' : states,
    }
    return render(request, 'accounts/add_address.html',context)

def ajax_load_district(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).all()
    context={
        'districts':districts
    }
    return render(request,'accounts/district_dropdown_option.html',context)


def edit_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id)
    states = State.objects.all()
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            if 'dashboard' in request.META.get('HTTP_REFERER', ''):
                return redirect('dashboard')
            else:
                return redirect('checkout')  
    else:
        form = AddressForm(instance=address)  

    context = {
        'form': form,
        'address': address,
        'states' : states,  
    }
    return render(request, 'accounts/edit_Address.html', context)

def delete_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id)
    address.delete()
    if 'checkout' in request.META.get('HTTP_REFERER', ''):
        return redirect('checkout')
    else:
        return redirect('dashboard') 
    
def wallet(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    if created:
        transaction =WalletTransaction.objects.create(
            wallet=wallet,
            amount=wallet.amount,
            transaction_type='Credit'
        )
        transaction.save()
    context = {
        'wallet' : wallet,
        'created': created,
    }
    return render(request, 'accounts/wallet.html',context)

def wallet_transaction(request):
    wallet = Wallet.objects.get(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-transaction_date')

        # Pagination
    paginator = Paginator(transactions, 10)  # Display 10 transactions per page
    page_number = request.GET.get('page')
    try:
            transactions = paginator.page(page_number)
    except PageNotAnInteger:
            transactions = paginator.page(1)
    except EmptyPage:
            transactions = paginator.page(paginator.num_pages)

    context = {
            'wallet': wallet,
            'transactions': transactions, 
        }
    return render(request, 'accounts/wallet_transaction.html', context)
    
