# -*- coding: utf-8 -*-
from django import template

from classytags.helpers import InclusionTag
from classytags.core import Options
from classytags.arguments import Argument

from shop.util.cart import get_or_create_cart


register = template.Library()


class Cart(InclusionTag):
    """
    Inclusion tag for displaying cart summary.
    """
    template = 'shop/templatetags/_cart.html'
    
    def get_context(self, context):
        cart = get_or_create_cart(context['request'])
        return {
            'cart': cart
        } 
register.tag(Cart)


class Order(InclusionTag):
    """
    Inclusio tag for displaying order.
    """
    template = 'shop/templatetags/_order.html'
    options = Options(
        Argument('order', resolve=True),
        )

    def get_context(self, context, order):
        return {
            'order': order
        } 
register.tag(Order)
