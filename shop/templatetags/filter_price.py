from django import template

register = template.Library()

@register.filter(name='filter_price')
def format_price(value):
    if int(value) == value:
        return f"{int(value)}"
    else:
        return f"{value:.2f}"