from . models import ProductAttribute,Wishlist
from django.db.models import Max, Min

def get_filter(request):

    minMaxPrice = ProductAttribute.objects.aggregate(Min('new_price'), Max('new_price'))

    data = {
        'minMaxPrice' : minMaxPrice
    }

    return data
def counter(request):
    wishlist_count = 0
    if request.user.is_authenticated and 'admin' not in request.path:
        try:
            wishlist = Wishlist.objects.filter(user=request.user)
            wishlist_count = wishlist.count()
        except Wishlist.DoesNotExist:
            wishlist_count = 0
    return {'wishlist_count': wishlist_count}