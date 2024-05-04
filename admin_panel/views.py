from django.shortcuts import render, get_object_or_404,redirect
from shop.models import Product,ProductImage, Size, Color, ProductAttribute,ProductOffer
from category.models import Category, Brand,CategoryOffer
from django.core.paginator import Paginator
from django.contrib import messages
from category.forms import CategoryForm,BrandForm,CategoryOfferForm
from shop.forms import ProductForm, ProductAttributeForm, SizeForm, ColorForm,ProductOfferForm
from accounts.models import Account
from django.contrib.auth.decorators import login_required
from orders.forms import CouponForm
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from orders.models import OrderProduct,Payment,Coupon,Order
from datetime import datetime,timedelta
from django.db.models import Sum,F
from datetime import date

# Decorator to check if the user is a superuser
def superuser_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/accounts/login/', 
    )
    return actual_decorator(view_func)

def show_sales_report(request):
    if request.method == 'POST':
        start_date_str = request.POST['startDate']
        end_date_str = request.POST['endDate']
        
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Filter OrderProduct objects based on ordered status and order status
    orders = Order.objects.filter(
    is_ordered=True,
    updated_at__date__range=[start_date, end_date],
    status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered']
    ).order_by('-updated_at')
    ordered_amount = 0
    sales_count = 0
    
    for i in orders:
        ordered_product = OrderProduct.objects.filter(order = i)
        total_products_ordered = ordered_product.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        i.quantity = total_products_ordered
        subtotal_order = 0

        for items in ordered_product:
            sales_count += items.quantity
            subtotal_order += items.quantity * items.product_price
           
        ordered_amount += i.order_total
        i.subtotal = subtotal_order     
    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'orders': orders ,
        'sales_count':sales_count,
        'ordered_amount':ordered_amount,
       
    }
    
    return render(request,'admin_panel/sales_report_pdf.html',context)

@superuser_required
def admin_home(request):
    # sales card
    filter_sales = request.GET.get('filter_sales', 'today')
    
    if filter_sales == 'today':
        today = timezone.now().date()
        sales_data = OrderProduct.objects.filter(
            order__created_at__date=today,
            ordered=True
        ).exclude(
        order__status__in=['Cancelled', 'Returned']
    )
        sales = sum(order.quantity for order in sales_data)
    elif filter_sales == 'month':
        month = timezone.now().month
        sales_data = OrderProduct.objects.filter(
            order__created_at__month=month,
            ordered=True
        ).exclude(
        order__status__in=['Cancelled', 'Returned']
    )
        sales = sum(order.quantity for order in sales_data)
    elif filter_sales == 'year':
        year = timezone.now().year
        sales_data = OrderProduct.objects.filter(
            order__created_at__year=year,
            ordered=True
        ).exclude(
        order__status__in=['Cancelled', 'Returned']
    )
        sales = sum(order.quantity for order in sales_data)
   
    # revenue card
    filter_revenue = request.GET.get('filter_revenue', 'today')
    
    if filter_revenue == 'today':
        today = timezone.now().date()
        revenue = Payment.objects.filter(
            updated_at__date=today,
            status='Paid'
        ).aggregate(total_revenue=Sum('amount_paid'))['total_revenue'] or 0
    elif filter_revenue == 'month':
        month = timezone.now().month
        revenue = Payment.objects.filter(
            updated_at__month=month,
            status='Paid'
        ).aggregate(total_revenue=Sum('amount_paid'))['total_revenue'] or 0
    elif filter_revenue == 'year':
        year = timezone.now().year
        revenue = Payment.objects.filter(
            updated_at__year=year,
            status='Paid'
        ).aggregate(total_revenue=Sum('amount_paid'))['total_revenue'] or 0
    # customer card
    filter_customers = request.GET.get('filter_customers', 'today')
    
    if filter_customers == 'today':
        today = timezone.now().date()
        customers_data = Account.objects.filter(
            created_at__date=today,
            is_active=True
        )
        customers = customers_data.count()
    elif filter_customers == 'month':
        month = timezone.now().month
        customers_data = Account.objects.filter(
            created_at__month=month,
            is_active=True
        )
        customers = customers_data.count()
    elif filter_customers == 'year':
        year = timezone.now().year
        customers_data = Account.objects.filter(
            created_at__year=year,
            is_active=True
        )
        customers = customers_data.count()
    
    # recent sales
    filter_recent_sales = request.GET.get('filter_recent_sales', 'today')
    
    if filter_recent_sales == 'today':
        today = timezone.now().date()
        recent_sales = OrderProduct.objects.filter(
            order__created_at__date=today,
            ordered=True
        ).order_by('-created_at') [:10]   
    elif filter_recent_sales == 'month':
        month = timezone.now().month
        recent_sales = OrderProduct.objects.filter(
            order__created_at__month=month,
            ordered=True
        ).order_by('-created_at')[:10]
    elif filter_recent_sales == 'year':
        year = timezone.now().year
        recent_sales = OrderProduct.objects.filter(
            order__created_at__year=year,
            ordered=True
        ).order_by('-created_at')[:10]

    
    filter_charts = request.GET.get('filter_charts', 'week')
    end_date = datetime.now()
    counts = []
    dates = []

    if filter_charts == 'week':
        start_date = end_date - timedelta(days=6)  
        daily_order_counts = (
            OrderProduct.objects
            .filter(order__created_at__range=(start_date, end_date), ordered=True, payment__status__in=['Paid', 'Pending'],
                    order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])  # Include Paid and Pending payments
            .values('order__created_at__date')
            .annotate(total_quantity=Sum('quantity'))  # Sum up the quantities of ordered items
            .order_by('order__created_at__date')
        )
        dates = [entry['order__created_at__date'].strftime('%Y-%m-%d') for entry in daily_order_counts]
        counts = [entry['total_quantity'] for entry in daily_order_counts]
    elif filter_charts == 'month':
        start_date = end_date - timedelta(days=30)  # Counting for 1 month
        daily_order_counts = (
            OrderProduct.objects
            .filter(order__created_at__range=(start_date, end_date), ordered=True, payment__status__in=['Paid', 'Pending'],
                    order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])  # Include Paid and Pending payments
            .values('order__created_at__date')
            .annotate(order_count=Sum('quantity'))
            .order_by('order__created_at__date')
        )
        counts = [sum(count['order_count'] for count in daily_order_counts[i:i + 7]) for i in range(0, len(daily_order_counts), 7)]
        dates = [f"Week {i+1}" for i in range(len(counts))]
    elif filter_charts == 'year':
        start_date = end_date - timedelta(days=365)  # Counting for 1 year
        monthly_order_counts = (
            OrderProduct.objects
            .filter(order__created_at__range=(start_date, end_date), ordered=True, payment__status__in=['Paid', 'Pending'],
                    order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])  # Include Paid and Pending payments
            .values('order__created_at__month')
            .annotate(order_count=Sum('quantity'))
            .order_by('order__created_at__month')
        )
        counts = [entry['order_count'] for entry in monthly_order_counts]
        dates = [f"Month {i+1}" for i in range(len(counts))]
    
    # top selling product
    product_quantities = (OrderProduct.objects
                                .filter(order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])
                                .values('product_attribute__product__name','product_attribute__image')
                                .annotate(total_quantity=Sum('quantity')))
                                

    product_revenues = OrderProduct.objects.values('product_attribute__product__name').annotate(
        total_revenue=Sum(F('quantity') * F('product_price')))

    top_product = []
    for product_quantity in product_quantities:
        name = product_quantity['product_attribute__product__name']
        image = product_quantity['product_attribute__image']
        total_quantity = product_quantity['total_quantity']
        total_revenue = next((product_revenue['total_revenue'] for product_revenue in product_revenues
                              if product_revenue['product_attribute__product__name'] == name), 0)
        top_product.append({'name': name, 'image':image, 'total_quantity': total_quantity, 'total_revenue': total_revenue})

    top_product.sort(key=lambda x: x['total_quantity'], reverse=True)

    top_selling_product = top_product[:10]

    # top selling category
    category_quantities = (OrderProduct.objects
                                .filter(order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])
                                .values('product__category__category_name','product__category__image').annotate(
                                total_quantity=Sum('quantity')))

    category_revenues = OrderProduct.objects.values('product__category__category_name').annotate(
        total_revenue=Sum(F('quantity') * F('product_price')))

    top_category = []
    for category_quantity in category_quantities:
        name = category_quantity['product__category__category_name']
        image = category_quantity['product__category__image']
        total_quantity = category_quantity['total_quantity']
        total_revenue = next((category_revenue['total_revenue'] for category_revenue in category_revenues
                              if category_revenue['product__category__category_name'] == name), 0)
        top_category.append({'name': name, 'image':image, 'total_quantity': total_quantity, 'total_revenue': total_revenue})

    top_category.sort(key=lambda x: x['total_quantity'], reverse=True)

    top_selling_category = top_category[:10]
    
    # top selling brand
    brand_quantities = (OrderProduct.objects
                                .filter(order__status__in=['Pending', 'Accepted', 'Shipped', 'Out For Delivery', 'Delivered'])
                        .values('product__brand__brand_name','product__brand__brand_image').annotate(
                        total_quantity=Sum('quantity')))

    brand_revenues = OrderProduct.objects.values('product__brand__brand_name').annotate(
        total_revenue=Sum(F('quantity') * F('product_price')))

    top_brands = []
    for brand_quantity in brand_quantities:
        brand_name = brand_quantity['product__brand__brand_name']
        brand_image = brand_quantity['product__brand__brand_image']
        total_quantity = brand_quantity['total_quantity']
        total_revenue = next((brand_revenue['total_revenue'] for brand_revenue in brand_revenues
                              if brand_revenue['product__brand__brand_name'] == brand_name), 0)
        top_brands.append({'brand_name': brand_name, 'brand_image':brand_image, 'total_quantity': total_quantity, 'total_revenue': total_revenue})

    top_brands.sort(key=lambda x: x['total_quantity'], reverse=True)

    top_selling_brands = top_brands[:10]

    context = {
            'admin_name': request.user,
            'sales':sales,
            'revenue':revenue,
            'filter_sales':filter_sales,
            'filter_revenue':filter_revenue,
            'customers':customers,
            'filter_customers':filter_customers,
            'filter_recent_sales':filter_recent_sales,
            'recent_sales':recent_sales,
            'counts':counts,
            'dates' : dates,
            'top_selling_brands':top_selling_brands,
            'top_selling_category':top_selling_category,
            'top_selling_product':top_selling_product

        }
 
    return render(request,'admin_panel/index.html',context)


@login_required(login_url='login')
def user_list(request):
    users=Account.objects.all().order_by('-id')
    users_count = users.count()

    page = request.GET.get('page', 1)
    user_paginator = Paginator(users, 15)
    users_page = user_paginator.get_page(page)

    context = {
            'users': users_page,
            'users_count': users_count,
        }
    return render(request, 'admin_panel/user_list.html', context)

@login_required(login_url='login')
def product_list(request):
    
    products = Product.objects.all().order_by('-created_date')

    products_count = products.count()
    page = request.GET.get('page', 1)
    product_paginator = Paginator(products, 15)
    products_page = product_paginator.get_page(page)

    context = {
        'products': products_page,
        'products_count': products_count,
    }
    return render(request, 'admin_panel/product_list.html', context)

from django.db import IntegrityError

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                category_id = request.POST.get('category')
                brand_id = request.POST.get('brand')

                name = request.POST.get('name')
                existing_product = Product.objects.filter(name__iexact=name, category_id=category_id, brand_id=brand_id).exists()
                category = get_object_or_404(Category, id=category_id)
                brand = Brand.objects.get(id=brand_id)
                if not category.list:
                    messages.error(request, f"The category '{category.category_name}' does not allow adding products.")
                elif brand.soft_delete:
                    messages.error(request, f"The brand '{brand.brand_name}' is not available right now.")
                elif existing_product:
                    messages.error(request, f"A product with the name '{name}' already exists.")
                else:
                    product.category = category
                    product.save()
                    messages.success(request, 'Product added successfully!')
                    return redirect('admin_product_list')
            except IntegrityError:
                messages.error (request,"A product with this name already exists. Please choose a different name.")
        else:
            messages.error(request, 'Failed to add product. Please check the form entries.')
    else:
        form = ProductForm()

    context = {'form': form}
    return render(request, 'admin_panel/add_product.html', context)


@login_required(login_url='login')
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                category_id = request.POST.get('category')
                brand_id = request.POST.get('brand')
                name = request.POST.get('name')
                existing_product = Product.objects.filter(name__iexact=name, category_id=category_id, brand_id=brand_id).exists()
                category = get_object_or_404(Category, id=category_id)
                if existing_product:
                    messages.error(request, f"A product with the name '{name}' already exists.")
                else:
                    product.category = category
                    product.save()
                    messages.success(request, 'Product added successfully!')
                    return redirect('admin_product_list')
            except IntegrityError:
                messages.error (request,"A product with this name already exists. Please choose a different name.")
        else:
            messages.error(request, 'Failed to add product. Please check the form entries.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/edit_product.html', {'form': form, 'product': product})

def delete_product(request,id):
    product=get_object_or_404(Product,id=id)
    if request.method == 'POST':        
        if product:
            product.delete()
            return redirect('admin_product_list')
    return render(request,'admin_panel/delete_product.html',{'product': product})

def list_product(request,product_id):
    product = get_object_or_404(Product,id = product_id)
    if request.method == 'POST':
        product.is_available = True
        product.save()

        return redirect('admin_product_list')

def soft_delete_product(request,product_id):
    product = get_object_or_404(Product,id = product_id)
    if request.method == 'POST':
        product.is_available = False
        product.save()
        return redirect('admin_product_list')
    
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['category_name']
 
            similar_category = Category.objects.filter(category_name__iexact=name).exists()
            if similar_category:
                messages.error(request, f"A category with the name '{name}' already exists.")
            else:
                form.save()
                messages.success(request, f"Added Category {name}")
                return redirect('admin_category_list')
        else:
            if 'image' in form.errors:
                messages.error(request, "Choose a valid image file")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.")
    else:
        form = CategoryForm()

    return render(request, 'admin_panel/add_category.html', {'form': form})

def admin_category_list(request):
    categories=Category.objects.all().order_by('-id')
    category_count = categories.count()

    page = request.GET.get('page', 1)
    category_paginator = Paginator(categories, 15)
    categories_page = category_paginator.get_page(page)

    context = {
            'categories': categories_page,
            'category_count': category_count,
        }
    return render(request, 'admin_panel/category_list.html', context)

def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            name = form.cleaned_data['category_name']
            similar_category = Category.objects.exclude(id=category_id).filter(category_name__iexact=name).exists()
            if similar_category:
                messages.error(request, f"A category with the name '{name}' already exists.")
            else:
                form.save()
                messages.success(request, f"Edited Category {name} successfully")
                return redirect('admin_category_list')
        else:
            if 'image' in form.errors:
                messages.error(request, "Choose a valid image file")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.")    
    form = CategoryForm(instance=category)

    context = {'form': form, 'category': category}
    return render(request, 'admin_panel/edit_category.html', context)

def delete_category(request,id):
    category=get_object_or_404(Category,id=id)
    if request.method == 'POST':        
        if category:
            category.delete()
            return redirect('admin_category_list')
    return render(request,'admin_panel/delete_category.html',{'category': category})

def unlisted_category(request,cat_id):
    category = get_object_or_404(Category,pk = cat_id)
    if request.method == 'POST':
        category.list = False
        category.save()
        print("saved",category.list)

        return redirect('admin_category_list')

def listed_category(request,cat_id):
    category = get_object_or_404(Category,pk = cat_id)
    if request.method == 'POST':
        category.list = True
        category.save()
        print("saved",category.list)
        return redirect('admin_category_list')

def block_user_admin(request, user_id):
    user = get_object_or_404(Account, pk=user_id)

    if request.method == 'POST':
        user.is_blocked = True
        user.save()
        messages.success(request, f'Successfully blocked user: {user.username}.')
    
    return redirect('user_list')

def unblock_user_admin(request, user_id):
    user = get_object_or_404(Account, pk=user_id)

    if request.method == 'POST':
        user.is_blocked = False
        user.save()
        messages.success(request, f'Successfully unblocked user: {user.username}.')
    
    return redirect('user_list')

def add_size(request):
    if request.method == 'POST':
        form = SizeForm(request.POST)
        if form.is_valid():
            size_title = request.POST.get('title')
            existing_size = Size.objects.filter(title__iexact=size_title).exists()
            if existing_size:
                messages.error(request, f"Size '{size_title}' already exists!")
            else:
                form.save()
                messages.success(request, f"Size '{size_title}' is added successfully!")
                return redirect('size_color')
    else:
        form = SizeForm()

    return render(request, 'admin_panel/add_size.html', {'form': form})

def add_color(request):
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            color_title = request.POST.get('title')
            color_code = request.POST.get('color_code')

            existing_color = Color.objects.filter(title__iexact=color_title).exists()
            existing_color_code = Color.objects.filter(color_code__iexact=color_code).exists()

            if existing_color:
                messages.error(request, f"Color '{color_title}' already exists!")
            elif existing_color_code:
                messages.error(request, f"Color code '{color_code}' already exists!")
            else:            
                form.save()
                messages.success(request, f"Color '{color_title}' is added successfully!")
                return redirect('size_color')
        else:
                messages.error(request, "Form is not valid. Please check the data you entered.") 
    else:
        form = ColorForm()
    return render(request, 'admin_panel/add_color.html', {'form': form})
 

def size_color_list(request):
    sizes = Size.objects.all().order_by('-id')
    colors = Color.objects.all().order_by('-id')
    context = {'sizes': sizes, 'colors': colors}
    return render(request, 'admin_panel/size_color.html', context)

def add_product_attribute(request):
    if request.method == 'POST':
        form = ProductAttributeForm(request.POST, request.FILES)
        if form.is_valid():
            new_attribute = form.save(commit=False)
            product_id = request.POST.get('product')
            existing_attributes = ProductAttribute.objects.filter(
                product=new_attribute.product,
                color=new_attribute.color,
                size=new_attribute.size,
            )
            product = Product.objects.get(id=product_id)
            if existing_attributes.exists():
                messages.error(request,"This product attribute already exists.")
                return render(request, 'admin_panel/add_product_attribute.html', {'form': form})
            elif not product.is_available:
                messages.error(request, f"The product '{product.name}' is not available right now.")
            elif new_attribute.stock <= 0:
                    new_attribute.is_available = False
            new_attribute.save()
            return redirect('variation_list')
        else:
            if 'image' in form.errors:
                messages.error(request, "Choose a valid image file")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.") 

    else:
        form = ProductAttributeForm()

    return render(request, 'admin_panel/add_product_attribute.html', {'form': form})

def variation_list(request):
    variants=ProductAttribute.objects.all().order_by('-created_date')
    variants_count = variants.count()
    for item in variants:
        if item.stock <= 0:
            item.is_available = False
            item.save()
        elif item.stock >= 0:
            item.is_available = True
            item.save()
    page = request.GET.get('page', 1)
    variants_paginator = Paginator(variants, 15)
    variants_page = variants_paginator.get_page(page)

    context = {
            'variants': variants_page,
            'variants_count': variants_count,
        }
    return render(request, 'admin_panel/variation_list.html', context)

def edit_variation(request, variation_id):
    variation = get_object_or_404(ProductAttribute, pk=variation_id)
    if request.method == 'POST':
        form = ProductAttributeForm(request.POST, request.FILES, instance=variation)
        if form.is_valid():
            product_id = request.POST.get('product')

            new_variation = form.save(commit=False)
            existing_variations = ProductAttribute.objects.filter(
                product=new_variation.product,
                color=new_variation.color,
                size=new_variation.size,
            ).exclude(pk=variation_id)  
            product = Product.objects.get(id=product_id)

            if existing_variations.exists():
                messages.error(request,"This product attribute already exists.")
                return render(request, 'admin_panel/edit_variation.html', {'form': form, 'variation': variation})
            elif not product.is_available:
                messages.error(request, f"The product '{product.name}' is not available right now.")          
            elif new_variation.stock <= 0:
                    new_variation.is_available = False       
            new_variation.save()
            return redirect('variation_list')
        else:
            if 'image' in form.errors:
                messages.error(request, "Choose a valid image file")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.") 
    else:
        form = ProductAttributeForm(instance=variation)

    context = {
        'form': form,
        'variation': variation,
    }
    return render(request, 'admin_panel/edit_variation.html', context)

def delete_variant(request,id):
    variant=get_object_or_404(ProductAttribute,id=id)
    if request.method == 'POST':        
        
        variant.delete()
        return redirect('variation_list')
       
    return render(request,'admin_panel/variation_list.html',{'variant': variant})

def unlisted_attribute(request,attr_id):
    attribute = get_object_or_404(ProductAttribute,id = attr_id)
    if request.method == 'POST':
        attribute.is_available = False
        attribute.save()
        return redirect('variation_list')

def listed_attribute(request,attr_id):
    attribute = get_object_or_404(ProductAttribute,id = attr_id)
    if request.method == 'POST':
        attribute.is_available = True
        attribute.save()
        return redirect('variation_list')

def product_images_list(request):
    products = Product.objects.filter(productattribute__isnull=False).distinct()

    context = {
            'products':products,   
        }
    return render(request, 'admin_panel/product_images_list.html', context)

def product_images(request,product_id):
    product = Product.objects.get(id = product_id)
    product_attributes = ProductAttribute.objects.filter(product = product)
    product_images = []  

    for attribute in product_attributes:
        attribute_images = ProductImage.objects.filter(product_attribute=attribute)
        product_images.extend(attribute_images)
    context = {
        'product_attributes' : product_attributes,
        'product_images' : product_images
    }

    return render(request, 'admin_panel/product_images.html', context)

def validate_image(file):
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return file.name.lower().endswith(allowed_extensions)

def add_product_images(request):
    product_attributes = ProductAttribute.objects.all()
    invalid_image = False
    valid_image = False
    context = {
        'product_attributes': product_attributes
    }
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        product_attribute_id = request.POST.get('product_attribute_id')      

        product_attributes = get_object_or_404(ProductAttribute, id = product_attribute_id)   
        for image in images:
            if validate_image(image):
                ProductImage.objects.create(product_attribute = product_attributes, image=image)
                valid_image = True
            else:
                invalid_image = True
        if invalid_image:
            messages.error(request,"Choose a valid image file")
            redirect('add_product_images')
        if valid_image:
            messages.success(request,"Successfully Added image file")

        return redirect('product_images' , product_id = product_attributes.product.id )

    return render(request, 'admin_panel/add_product_images.html',context)

@login_required(login_url='login')
def delete_images(request, id):
    image = get_object_or_404(ProductImage, id=id)

    if request.method == 'POST':
        product_id = image.product_attribute.product.id  # Assuming product_id is accessible this way
        image.delete()
        return redirect('product_images', product_id=product_id)

    return render(request, 'admin_panel/variation_list.html', {'image': image})

def add_brand(request):
    for i in Brand.objects.all():
        print(i.brand_name)
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            name = request.GET.get('brand_name')
            existing_brand = Brand.objects.filter(brand_name__iexact = name).exists()
            if existing_brand:
                messages.error(request,"This brand already exists.")
            else:
                form.save()
                return redirect('brand_list')
        else:
            if 'brand_image' in form.errors:
                messages.error(request, "Choose a valid image file")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.")
    else:
        form = BrandForm()

    context ={
        'form': form,
    }

    return render(request, 'admin_panel/add_brand.html', context)

def edit_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            name = form.cleaned_data['brand_name']
            existing_brand = Brand.objects.filter(brand_name__iexact=name).exclude(id=brand_id).exists()
            if existing_brand:
                messages.error(request, "This brand already exists.")
            else:
                form.save()
                messages.success(request, "Brand updated successfully.")
                return redirect('brand_list')
        else:
            if 'brand_image' in form.errors:
                messages.error(request, "Choose a valid image file.")
            else:
                messages.error(request, "Form is not valid. Please check the data you entered.")
    else:
        form = BrandForm(instance=brand)

    context = {
        'form': form,
        'brand':brand,
        }
    return render(request, 'admin_panel/edit_brand.html', context)

def brand_list(request):
    brand = Brand.objects.all().order_by('-id')
    
    brand_count = brand.count()
    page = request.GET.get('page', 1)
    brand_paginator = Paginator(brand, 20)
    brand_page = brand_paginator.get_page(page)
    context = {
     'brand' : brand_page,
     'brand_count' : brand_count   
    }

    return render(request, 'admin_panel/brand_list.html', context)

def unlist_brand(request,brand_id):
    brand = get_object_or_404(Brand,id = brand_id)
    if request.method == 'POST':
        brand.soft_delete = False
        brand.save()

        return redirect('brand_list')

def soft_delete_brand(request,brand_id):
    brand = get_object_or_404(Brand,id = brand_id)
    if request.method == 'POST':
        brand.soft_delete = True
        brand.save()
        return redirect('brand_list')
    
def list_orders(request):
    orders = Order.objects.filter(is_ordered = True).order_by('-id')
    orders_count = orders.count()
    page = request.GET.get('page', 1)
    orders_paginator = Paginator(orders, 20)
    orders_page = orders_paginator.get_page(page)
    context = {
     'orders' : orders_page,
     'orders_count' : orders_count   
    }
    return render(request, 'admin_panel/list_orders.html',context)

@login_required
def update_order_status(request, order_id, status):
    order = get_object_or_404(Order, pk=order_id)
    

    if status in [choice[0] for choice in Order.STATUS]:
        order.status = status
        order.updated_at = timezone.now()
        if order.payment.status == 'Failed':
            # Handle failed payment scenario
            messages.error(request, "Payment for this order has failed. Please check your payment status.")
        else:
            products_in_stock = True
            order_products = OrderProduct.objects.filter(order=order)
            for order_product in order_products:
                if order_product.product_attribute.stock < order_product.quantity:
                    products_in_stock = False
                    messages.error(request, f"Not enough stock available for {order_product.product.name}.")

            if products_in_stock:
                order.save()
                order.payment.amount_paid = sum(order_product.product_price * order_product.quantity for order_product in order_products)
                order.payment.status = 'Paid'
                order.payment.updated_at = timezone.now()
                order.payment.save()
                messages.success(request, f"Payment status for Order #{order.order_number} updated to 'Paid'.")
                messages.success(request, f"Order #{order.order_number} has been updated to '{status}' status.")

                # Mark products as ordered if payment is 'Paid'
                for order_product in order_products:
                    order_product.ordered = True
                    order_product.save()
            else:
                messages.error(request, "Order cannot be completed due to insufficient stock.")
    else:
        messages.error(request, f"Invalid status: {status}")
    return redirect('list_orders')

@login_required
def admin_order_details(request, order_id):
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    order = Order.objects.get(is_ordered=True, id=order_id)
    
    payment = Payment.objects.get(order__id=order_id)
    subtotal = 0
    for order_product in order_products:
        total = order_product.quantity * order_product.product_price
        order_product.total = total
        subtotal += total
    context = {
        'order_products': order_products,
        'order': order,
        'payment': payment,
        'subtotal':subtotal
    }

    return render(request, 'admin_panel/admin_order_details.html', context)

def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)  
            if coupon.discount <= coupon.minimum_amount // 10:
                if coupon.expiration_date >= date.today():
                    coupon.coupon_code = Coupon.generate_coupon_code()
                    coupon.save()
                    return redirect('coupon_list')
                else:
                    messages.error(request, "Coupon expiration date should be in the future.")
            else:
                messages.error(request, "Discount amount should be less than or equal to 10% of the minimum amount.")
    else:
        form = CouponForm()

    context = {
        'form':form
    }
    return render(request, 'admin_panel/add_coupon.html', context)

def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-id')
    current_datetime = timezone.now()

    for coupon in coupons:
        if coupon.expiration_date < current_datetime.date():
            coupon.active = False
            coupon.save()
        if coupon.max_usage == coupon.used_count:
            coupon.active = False
            coupon.save()
    coupon_count = coupons.count()
    context = {
        'coupons':coupons,
        'coupon_count':coupon_count
    }
    return render(request, 'admin_panel/coupon_list.html' ,context)

def delete_coupon(request,coupon_id):
    coupon = Coupon.objects.get(id = coupon_id)
    if request.method == 'POST':
        coupon.delete()
        messages.success(request,'Deleted coupon successfully')
        return redirect('coupon_list')


def unlist_coupon(request,coupon_id):
    coupon = get_object_or_404(Coupon,id = coupon_id)
    if request.method == 'POST':
        coupon.active = False
        coupon.save()

        return redirect('coupon_list')

def list_coupon(request,coupon_id):
    coupon = get_object_or_404(Coupon,id = coupon_id)
    if request.method == 'POST':
        coupon.active = True
        coupon.save()
        return redirect('coupon_list')

def add_product_offer(request):
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            start_date = timezone.now().date()
            end_date = form.cleaned_data['end_date']
            if end_date >= start_date:
                product_id = form.cleaned_data['product'].id
                existing_offer = ProductOffer.objects.filter(product_id=product_id, is_active=True).exists()
                if not existing_offer:
                    discount_percentage = form.cleaned_data['discount_percentage']
                    if discount_percentage < 90:  
                        form.save()
                        messages.success(request, 'Successfully added product offer')
                        return redirect('product_offer_list')
                    else:
                        messages.error(request, 'Discount percentage cannot be greater than or equal to 90%.')
                else:
                    messages.error(request, 'An active offer for this product already exists.')
            else:
                messages.error(request, "Please ensure that the choosen date is today's or future's date")
    else:
        form = ProductOfferForm()
    context = {
        'form': form,
    }
    return render(request, 'admin_panel/add_product_offer.html', context)

def edit_product_offer(request,p_offer_id):
    p_offer = ProductOffer.objects.get(id =p_offer_id )
    if request.method == 'POST':
        form = ProductOfferForm(request.POST,instance=p_offer)
        if form.is_valid():
            start_date = timezone.now().date()
            end_date = form.cleaned_data['end_date']
            if end_date >= start_date:
                product_id = form.cleaned_data['product'].id
                existing_offer = ProductOffer.objects.filter(product_id=product_id, is_active=True).exists()
                if not existing_offer:
                    discount_percentage = form.cleaned_data['discount_percentage']
                    if discount_percentage < 90:
                        product_offer = form.save(commit=False)
                        product_offer.is_active = True  # Set is_active to True
                        product_offer.save()
                        messages.success(request,'successfully updated product offer')
                        return redirect('product_offer_list')
                    else:
                        messages.error(request, 'Discount percentage cannot be greater than or equal to 90%.')
                else:
                    messages.error(request, 'An active offer for this product already exists.')
            else:
                messages.error(request, "Please ensure that the choosen date is today's or future's date")
                return redirect('edit_product_offer', p_offer.id)
    else:
        form = ProductOfferForm(instance=p_offer)
    context = {
        'form': form,
        'p_offer':p_offer
    }
    return render(request, 'admin_panel/edit_product_offer.html', context)

def product_offer_list(request):
    p_offers = ProductOffer.objects.all().order_by('-id')
    current_datetime = datetime.now()

    for offer in p_offers:
        if offer.end_date < current_datetime.date():
            offer.is_active = False
            offer.save()
    return render(request, 'admin_panel/product_offer_list.html',{'p_offers':p_offers})

def add_category_offer(request):
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            start_date = timezone.now().date()
            end_date = form.cleaned_data['end_date']
            if end_date >= start_date:
                category_id = form.cleaned_data['category'].id
                existing_offer = CategoryOffer.objects.filter(category_id=category_id, is_active=True).exists()
                if not existing_offer:
                    discount_percentage = form.cleaned_data['discount_percentage']
                    if discount_percentage < 90:
                        form.save()
                        messages.success(request,'successfully added category offer')
                        return redirect('category_offer_list')
                    else:
                        messages.error(request, 'Discount percentage cannot be greater than or equal to 90%.')
                else:
                    messages.error(request, 'An active offer for this category already exists.')
            else:
                messages.error(request, "Please ensure that the choosen date is today's or future's date")
    else:
        form = CategoryOfferForm()
    context = {
        'form': form,
    }
    return render(request, 'admin_panel/add_category_offer.html', context)

def edit_category_offer(request,cat_offer_id):
    cat_offer = CategoryOffer.objects.get(id =cat_offer_id )
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST,instance=cat_offer)
        if form.is_valid():
            start_date = timezone.now().date()
            end_date = form.cleaned_data['end_date']
            if end_date >= start_date:
                category_id = form.cleaned_data['category'].id
                existing_offer = CategoryOffer.objects.filter(category_id=category_id, is_active=True).exists()
                if not existing_offer:
                    discount_percentage = form.cleaned_data['discount_percentage']
                    if discount_percentage < 90:
                        category_offer = form.save()
                        category_offer.is_active = True
                        category_offer.save()
                        messages.success(request,'successfully updated category offer')
                        return redirect('category_offer_list')
                    else:
                        messages.error(request, 'Discount percentage cannot be greater than or equal to 90%.')
                else:
                    messages.error(request, 'An active offer for this category already exists.')
            else:
                messages.error(request, "Please ensure that the choosen date is today's or future's date")
                return redirect('edit_category_offer', cat_offer.id)
    else:
        form = CategoryOfferForm(instance=cat_offer)
    context = {
        'form': form,
        'cat_offer':cat_offer
    }
    return render(request, 'admin_panel/edit_category_offer.html', context)

def category_offer_list(request):
    c_offers = CategoryOffer.objects.all().order_by('-id')
    current_datetime = timezone.now()
    for offer in c_offers:
        if offer.end_date < current_datetime.date():
            offer.is_active = False
            offer.save()

    return render(request, 'admin_panel/category_offer_list.html',{'c_offers':c_offers})

def unlist_category_offer(request,cat_id):
    category_offer = get_object_or_404(CategoryOffer,pk = cat_id)
    if request.method == 'POST':
        category_offer.is_active = False
        category_offer.save()

        return redirect('category_offer_list')

def list_category_offer(request,cat_id):
    category_offer = get_object_or_404(CategoryOffer,pk = cat_id)
    if request.method == 'POST':
        category = category_offer.category
        if not category.categoryoffer_set.filter(is_active=True).exists():
            category_offer.is_active = True
            category_offer.save()
        else:
            messages.error(request, 'This category already has an active offer.')
        return redirect('category_offer_list')
    
def unlist_product_offer(request,p_offer_id):
    product_offer = get_object_or_404(ProductOffer,pk = p_offer_id)
    if request.method == 'POST':
        product_offer.is_active = False
        product_offer.save()

        return redirect('product_offer_list')

def list_product_offer(request,p_offer_id):
    product_offer = get_object_or_404(ProductOffer,pk = p_offer_id)
    if request.method == 'POST':
        product = product_offer.product
        if not product.productoffer_set.filter(is_active=True).exists():
            product_offer.is_active = True
            product_offer.save()
        else:
            messages.error(request, 'This product already has an active offer.')
        return redirect('product_offer_list')