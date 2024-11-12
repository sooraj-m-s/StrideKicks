from django import template

register = template.Library()

@register.filter
def min_value(value, arg):
    return min(value, arg)
