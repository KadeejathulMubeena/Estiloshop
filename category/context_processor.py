from .models import Category

def menu_links(request):
    
    links=Category.objects.filter(list = True)
    return dict(links=links)