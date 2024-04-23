from django.shortcuts import render
from category.models import Category,Brand
from django.db.models import Count, Exists, OuterRef
from shop.models import Product,ProductAttribute
from datetime import datetime



def home(request):
    categories = Category.objects.annotate(
    product_count=Count('product', filter=Exists(
        Product.objects.filter(
            category_id=OuterRef('pk'),
            productattribute__product_id=OuterRef('product__id')  # Assuming ProductAttribute has a ForeignKey to Product
        )
    ))
)
    products=Product.objects.filter(is_available=True).order_by('-created_date')[:9]
    brands=Brand.objects.annotate(product_count=Count('product')).order_by('-id')
    products_with_attributes = []  

    for product in products:
        attributes = ProductAttribute.objects.filter(product=product)
        if attributes.exists():  # Check if the product has attributes
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
                'discount_percentage':discount_percentage,
                'product_offer':product_offer,
                'category_offer':category_offer,
                'c_remaining_days':c_remaining_days,
                'p_remaining_days':p_remaining_days
            })

    context={
        'categories':categories,
        'products':products,
        'brands' : brands,
        'products_with_attributes' : products_with_attributes
    }
    return render(request,'shop/index.html',context)