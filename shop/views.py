# views.py
from django.shortcuts import render, get_object_or_404,redirect
from .models import Product,ProductAttribute, Size, Color, ProductImage,Wishlist,ProductOffer
from category.models import Category,Brand,CategoryOffer
from django.core.paginator import Paginator
from scarts.models import CartItem
from scarts.views import _cart_id
from django.db.models import Q , Count,Min,Max
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core import serializers
from django.db.models import Subquery, OuterRef
from django.contrib.auth.decorators import login_required
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def list_products(request, category_slug=None):
    categories = None
    products_with_attributes = []

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories,
            is_available=True,
            category__list=True,
            brand__soft_delete=False,
        )
    else:
        products = Product.objects.filter(
            category__list=True,
            brand__soft_delete=False,
            is_available=True,
        )

    for product in products:
        attributes = ProductAttribute.objects.filter(product=product)
        if attributes.exists():
            first_attribute = attributes.first()
            discounts = first_attribute.calculate_discounted_price()
            discount_percentage = discounts['discount_percentage']
            category_offer = discounts['category_offer']
            product_offer = discounts['product_offer']
            c_remaining_days = 0
            if category_offer and category_offer.end_date > datetime.now().date():
                c_remaining_days = (category_offer.end_date - datetime.now().date()).days
            p_remaining_days = 0
            if product_offer and product_offer.end_date > datetime.now().date():
                p_remaining_days = (product_offer.end_date - datetime.now().date()).days

            products_with_attributes.append({
                'product': product,
                'first_attribute': first_attribute,
                'discount_percentage': discount_percentage,
                'product_offer': product_offer,
                'category_offer': category_offer,
                'c_remaining_days': c_remaining_days,
                'p_remaining_days': p_remaining_days,
            })

    products_count = len(products_with_attributes)
    page = request.GET.get('page', 1)
    product_paginator = Paginator(products_with_attributes, 9)
    products_page = product_paginator.get_page(page)

    context = {
        'products_with_attributes': products_page,
        'products_count': products_count,
        'categories': categories,
    }
    return render(request, 'shop/shop.html', context)

def filter_products(request):
    # Extract the selected price range values from the request
    price_ranges = {
        'below_1000': (0, 1000),
        '1000_to_2000': (1000, 2000),
        '2000_to_3000': (2000, 3000),
        '3000_to_4000': (3000, 4000),
        '4000_to_5000': (4000, 5000),
    }
    selected_ranges = [key for key in price_ranges.keys() if key in request.GET]

    if not selected_ranges:
        return redirect('shop')

    # Construct Q objects for filtering products based on price ranges
    filtered_products = Product.objects.filter(
        category__list=True,
        brand__soft_delete=False,
        is_available=True,
    )
    products_with_attributes = []

    # Apply price filters
    for product in filtered_products:
        product_attributes = ProductAttribute.objects.filter(product=product)
        if product_attributes.exists():
            first_attribute = product_attributes.first()
            discounts = first_attribute.calculate_discounted_price()
            discount_percentage = discounts['discount_percentage']
            category_offer = discounts['category_offer']
            product_offer = discounts['product_offer']
            c_remaining_days = 0
            if category_offer and category_offer.end_date > datetime.now().date():
                c_remaining_days = (category_offer.end_date - datetime.now().date()).days
            p_remaining_days = 0
            if product_offer and product_offer.end_date > datetime.now().date():
                p_remaining_days = (product_offer.end_date - datetime.now().date()).days
            # Check if offer price is available, if not, use regular price
            price_to_use = first_attribute.offer_price if first_attribute.offer_price else first_attribute.price

            # Check if the price falls within the selected price ranges
            for price_range_key in selected_ranges:
                min_price, max_price = price_ranges[price_range_key]
                if min_price <= price_to_use <= max_price:
                    products_with_attributes.append({
                        'product': product,
                        'first_attribute': first_attribute,
                        'price_to_use': price_to_use,
                        'discount_percentage': discount_percentage,
                        'product_offer': product_offer,
                        'category_offer': category_offer,
                        'c_remaining_days': c_remaining_days,
                        'p_remaining_days': p_remaining_days
                    })
                    break  # Exit the loop once a price range match is found

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(products_with_attributes, 9)
    products_page = paginator.get_page(page_number)

    context = {
        'products_with_attributes': products_page,
        'products_count': paginator.count,
    }

    return render(request, 'shop/shop.html', context)

def search(request):
    keyword = request.GET.get('keyword')
    products_with_attributes = []

    if keyword:
        # Filter products based on keyword
        products = Product.objects.filter(Q(description__icontains=keyword) | Q(name__icontains=keyword),category__list = True,brand__soft_delete = False,is_available=True).order_by('created_date')

        # Fetch products with attributes for the filtered products
        for product in products:
            product_attributes = ProductAttribute.objects.filter(product=product)
            if product_attributes.exists():
                first_attribute =product_attributes.first()
                discounts = first_attribute.calculate_discounted_price()
                offer_price = discounts['final_price']
                discount_percentage = discounts['discount_percentage']
                category_offer = discounts['category_offer']
                product_offer = discounts['product_offer']
                c_remaining_days = 0
                if category_offer and category_offer.end_date > datetime.now().date():
                    c_remaining_days = (category_offer.end_date - datetime.now().date()).days
                p_remaining_days = 0
                if product_offer and product_offer.end_date > datetime.now().date():
                    p_remaining_days = (product_offer.end_date - datetime.now().date()).days

                products_with_attributes.append({
                    'product': product,
                    'first_attribute': first_attribute,
                    'offer_price': offer_price,
                    'discount_percentage':discount_percentage,
                    'product_offer':product_offer,
                    'category_offer':category_offer,
                    'c_remaining_days':c_remaining_days,
                    'p_remaining_days':p_remaining_days  
                })
        products_count = len(products_with_attributes)
        

    context = {
        'products_with_attributes': products_with_attributes,
        'products_count':products_count,
       
    }

    return render(request, 'shop/shop.html', context)

def shop_latest(request):

    latest_products = Product.objects.filter(category__list = True,brand__soft_delete = False,is_available=True).order_by('-created_date')

    products_with_attributes = []
    for product in latest_products:
        product_attributes = ProductAttribute.objects.filter(product=product)
        if product_attributes.exists():
            first_attribute =product_attributes.first()
            discounts = first_attribute.calculate_discounted_price()
            discount_percentage = discounts['discount_percentage']
            category_offer = discounts['category_offer']
            product_offer = discounts['product_offer']
            c_remaining_days = 0
            if category_offer and category_offer.end_date > datetime.now().date():
                c_remaining_days = (category_offer.end_date - datetime.now().date()).days
            p_remaining_days = 0
            if product_offer and product_offer.end_date > datetime.now().date():
                p_remaining_days = (product_offer.end_date - datetime.now().date()).days
            products_with_attributes.append({
                'product': product,
                'first_attribute': first_attribute,
                'discount_percentage':discount_percentage,
                'product_offer':product_offer,
                'category_offer':category_offer,
                'c_remaining_days':c_remaining_days,
                'p_remaining_days':p_remaining_days  
            })

    page_number = request.GET.get('page', 1)
    paginator = Paginator(products_with_attributes, 9)
    products_page = paginator.get_page(page_number)

    context = {
        'products_with_attributes': products_page,
        'products_count': paginator.count,
    }

    return render(request, 'shop/shop.html', context)

def low_to_high(request):
    low_high_products = Product.objects.filter(category__list = True,brand__soft_delete = False,is_available=True)

    products_with_attributes = []
    for product in low_high_products:
        product_attributes = ProductAttribute.objects.filter(product=product)
        if product_attributes.exists():
            first_attribute = product_attributes.first()
            discounts = first_attribute.calculate_discounted_price()
            discount_percentage = discounts['discount_percentage']
            category_offer = discounts['category_offer']
            product_offer = discounts['product_offer']
            c_remaining_days = 0
            if category_offer and category_offer.end_date > datetime.now().date():
                c_remaining_days = (category_offer.end_date - datetime.now().date()).days
            p_remaining_days = 0
            if product_offer and product_offer.end_date > datetime.now().date():
                p_remaining_days = (product_offer.end_date - datetime.now().date()).days
            # Check if offer price is available, else use regular price
            price_to_use = first_attribute.offer_price if first_attribute.offer_price else first_attribute.price
            products_with_attributes.append({
                'product': product,
                'first_attribute': first_attribute,
                'discount_percentage': discount_percentage,
                'product_offer': product_offer,
                'category_offer': category_offer,
                'c_remaining_days': c_remaining_days,
                'p_remaining_days': p_remaining_days,
                'price_to_use': price_to_use
            })

    products_with_attributes.sort(key=lambda x: x['price_to_use'])

    page_number = request.GET.get('page', 1)
    paginator = Paginator(products_with_attributes, 9)
    products_page = paginator.get_page(page_number)

    context = {
        'products_with_attributes': products_page,
        'products_count': paginator.count,
    }

    return render(request, 'shop/shop.html', context)

def high_to_low(request):

    high_low_products = Product.objects.filter(category__list = True,brand__soft_delete = False,is_available=True)

    products_with_attributes = []
    for product in high_low_products:
        product_attributes = ProductAttribute.objects.filter(product=product)
        if product_attributes.exists():
            first_attribute = product_attributes.first()
            discounts = first_attribute.calculate_discounted_price()
            discount_percentage = discounts['discount_percentage']
            category_offer = discounts['category_offer']
            product_offer = discounts['product_offer']
            c_remaining_days = 0
            if category_offer and category_offer.end_date > datetime.now().date():
                c_remaining_days = (category_offer.end_date - datetime.now().date()).days
            p_remaining_days = 0
            if product_offer and product_offer.end_date > datetime.now().date():
                p_remaining_days = (product_offer.end_date - datetime.now().date()).days
            # Check if offer price is available, else use regular price
            price_to_use = first_attribute.offer_price if first_attribute.offer_price else first_attribute.price
            products_with_attributes.append({
                'product': product,
                'first_attribute': first_attribute,
                'discount_percentage': discount_percentage,
                'product_offer': product_offer,
                'category_offer': category_offer,
                'c_remaining_days': c_remaining_days,
                'p_remaining_days': p_remaining_days,
                'price_to_use': price_to_use
            })

    products_with_attributes.sort(key=lambda x: x['price_to_use'], reverse=True)

    page_number = request.GET.get('page', 1)
    paginator = Paginator(products_with_attributes, 9)
    products_page = paginator.get_page(page_number)

    context = {
        'products_with_attributes': products_page,
        'products_count': paginator.count,
    }

    return render(request, 'shop/shop.html', context)

def product_detail(request, category_slug, product_slug):
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
    attributes = ProductAttribute.objects.filter(product=product)
    first_attribute = attributes.first()
    sizes = attributes.values_list('size__id', 'size__title').distinct()
    colors = attributes.values_list('color__id', 'color__title', 'color__color_code').distinct()

    multiple_images = None
    selected_attribute = None
    if is_ajax(request=request) and request.method == 'GET':
        size_id = request.GET.get('size_id')
        color_id = request.GET.get('color_id')
        if size_id and color_id:
            try:
                selected_attribute = attributes.get(size__id=size_id, color__id=color_id)
                discounts = selected_attribute.calculate_discounted_price()
                data = {
                    'price': selected_attribute.price,
                    'stock':selected_attribute.stock,
                    'offer_price' : selected_attribute.offer_price,
                    'discount_percentage': discounts['discount_percentage'],
                    'image_url': selected_attribute.image.url if selected_attribute.image else None,
                    'product_images': [image.image.url for image in selected_attribute.multiple_images.all()],
                    'stock': selected_attribute.stock,
                }
                return JsonResponse({'selected_attribute': data})
            except ProductAttribute.DoesNotExist:
                return JsonResponse({'error': 'Selected attribute not found'}, status=404)

    if not multiple_images and first_attribute:
        multiple_images = ProductImage.objects.filter(product_attribute=first_attribute)
    
    discounts = first_attribute.calculate_discounted_price()
    discount_percentage = discounts['discount_percentage']
    
    context = {
        'product': product,
        'attributes': attributes,
        'first_attribute': first_attribute,
        'discount_percentage':discount_percentage,
        'sizes': sizes,
        'colors': colors,
        'selected_attribute': selected_attribute,
        'multiple_images':multiple_images
    }
    return render(request, 'shop/product_detail.html', context)

def get_available_colors(request):
    product_id = request.GET.get('product_id')  
    size_id = request.GET.get('size_id')
    
    if product_id and size_id:
        try:
            # Get available colors for the selected size and product
            product_attributes = ProductAttribute.objects.filter(product_id=product_id, size_id=size_id)
            colors = Color.objects.filter(id__in=product_attributes.values_list('color_id', flat=True)).distinct().values('id', 'title')
            return JsonResponse({'colors': list(colors)})
        except ProductAttribute.DoesNotExist:
            return JsonResponse({'colors': []})  # No colors available for the selected size and product
    else:
        return JsonResponse({'error': 'Product ID or Size ID not provided'})
    
@login_required
def add_wishlist(request, product_id):
    attributes = ProductAttribute.objects.filter(product__id=product_id)
    attribute = attributes.first()
    
    if Wishlist.objects.filter(user=request.user, items=attribute).exists():
        return redirect('wishlist')
    
    wishlist = Wishlist.objects.create(user=request.user, items=attribute)
    
    wishlist.save()
    return redirect('wishlist')
    

@login_required
def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
    else:
        # Handle anonymous user or other cases as needed
        wishlist_items = []
    context = {
        'wishlist_items': wishlist_items
        }
    return render(request, 'shop/wishlist.html', context)

@login_required
def delete_wishlist(request, wishlist_id):
    if request.method == 'POST':
        wishlist = Wishlist.objects.get(id=wishlist_id)
        if wishlist:
            wishlist.delete()
    return redirect('wishlist')
