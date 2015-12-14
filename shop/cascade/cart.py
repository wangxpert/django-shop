# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.forms import widgets
from django.template.loader import select_template, get_template
from django.utils.translation import ugettext_lazy as _
from django.utils.html import mark_safe
from cms.plugin_pool import plugin_pool
from cmsplugin_cascade.fields import PartialFormField
from shop import settings as shop_settings
from shop.models.cart import CartModel
from shop.rest.serializers import CartSerializer
from .plugin_base import ShopPluginBase


class ShopCartPlugin(ShopPluginBase):
    name = _("Cart")
    require_parent = True
    parent_classes = ('BootstrapColumnPlugin',)
    cache = False
    CHOICES = (('editable', _("Editable Cart")), ('static', _("Static Cart")),
        ('summary', _("Cart Summary")), ('watch', _("Watch List")),)
    glossary_fields = (
        PartialFormField('render_type',
            widgets.RadioSelect(choices=CHOICES),
            label=_("Render as"),
            initial='editable',
            help_text=_("Shall the cart be editable or a static summary?"),
        ),
    )

    @classmethod
    def get_identifier(cls, instance):
        render_type = instance.glossary.get('render_type')
        return mark_safe(dict(cls.CHOICES).get(render_type, ''))

    def get_render_template(self, context, instance, placeholder):
        render_template = instance.glossary.get('render_template')
        if render_template:
            return get_template(render_template)
        render_type = instance.glossary.get('render_type')
        if render_type == 'static':
            template_names = [
                '{}/cart/static.html'.format(shop_settings.APP_LABEL),
                'shop/cart/static.html',
            ]
        elif render_type == 'summary':
            template_names = [
                '{}/cart/summary.html'.format(shop_settings.APP_LABEL),
                'shop/cart/summary.html',
            ]
        elif render_type == 'watch':
            template_names = [
                '{}/cart/watch.html'.format(shop_settings.APP_LABEL),
                'shop/cart/watch.html',
            ]
        else:
            template_names = [
                '{}/cart/editable.html'.format(shop_settings.APP_LABEL),
                'shop/cart/editable.html',
            ]
        return select_template(template_names)

    def render(self, context, instance, placeholder):
        render_type = instance.glossary.get('render_type')
        if render_type in ('static', 'summary',):
            # update context for static and summary cart rendering since items are rendered in HTML
            cart = CartModel.objects.get_from_request(context['request'])
            if cart:
                cart_serializer = CartSerializer(cart, context=context, label='cart')
                context['cart'] = cart_serializer.data
                if render_type == 'summary':
                    # for a cart summary we're only interested into the number of items
                    context['cart']['items'] = len(context['cart']['items'])
        else:
            context['ng_model_options'] = shop_settings.EDITCART_NG_MODEL_OPTIONS
        return super(ShopCartPlugin, self).render(context, instance, placeholder)

plugin_pool.register_plugin(ShopCartPlugin)
