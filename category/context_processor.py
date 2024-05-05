from .models import Category

def menu_links(request):

    links=Category.objects.filter(list=True, product__brand__soft_delete=False,product__is_available = True).distinct()
    return dict(links=links)