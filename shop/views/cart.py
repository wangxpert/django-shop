# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.cache import add_never_cache_headers
from django.utils.module_loading import import_by_path
from rest_framework.decorators import list_route
from rest_framework import viewsets
from shop import settings as shop_settings
from shop.models.cart import CartModel, CartItemModel
from shop.rest import serializers
from shop.modifiers.pool import cart_modifiers_pool


class BaseViewSet(viewsets.ModelViewSet):
    paginate_by = None

    def get_queryset(self):
        cart = CartModel.objects.get_from_request(self.request)
        if self.kwargs.get(self.lookup_field):
            # we're interest only into a certain cart item
            return CartItemModel.objects.filter(cart=cart)
        # otherwise the CartSerializer will show its detail and list all its items
        return cart

    def get_serializer(self, *args, **kwargs):
        kwargs.update(context=self.get_serializer_context(), label=self.serializer_label)
        many = kwargs.pop('many', False)
        if many or self.item_serializer_class is None:
            return self.serializer_class(*args, **kwargs)
        return self.item_serializer_class(*args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """Set HTTP headers to not cache this view"""
        if self.action != 'render_product_summary':
            add_never_cache_headers(response)
        return super(BaseViewSet, self).finalize_response(request, response, *args, **kwargs)


class CartViewSet(BaseViewSet):
    serializer_label = 'cart'
    serializer_class = serializers.CartSerializer
    item_serializer_class = serializers.CartItemSerializer


class WatchViewSet(BaseViewSet):
    serializer_label = 'watch'
    serializer_class = serializers.WatchSerializer
    item_serializer_class = serializers.WatchItemSerializer


# TODO: move this into views/checkout.py
class CheckoutViewSet(BaseViewSet):
    serializer_label = 'checkout'
    serializer_class = serializers.CheckoutSerializer
    item_serializer_class = None

    def __init__(self, **kwargs):
        super(CheckoutViewSet, self).__init__(**kwargs)
        self.dialog_forms = []
        for form_class in shop_settings.DIALOG_FORMS:
            self.dialog_forms.append(import_by_path(form_class))

    @list_route(methods=['post'], url_path='update')
    def update(self, request):
        """
        All forms using the AngularJS directive `shop-dialog-form` have an implicit scope containing
        an `update()` function. This function then may be connected to any input element, say
        `ng-change="update()"`. If such an event triggers, the scope data is send to this
        method using an Ajax POST request. This `update()` method then dispatches the form data
        to all forms registered in `settings.SHOP_DIALOG_FORMS`.
        Afterwards the cart is updated, so that all cart modifiers run and adopt those changes.
        """
        cart = self.get_queryset()
        errors = {}
        # iterate over all given forms and collect potential errors
        for form_class in self.dialog_forms:
            data = request.data.get(form_class.identifier)
            reply = form_class.form_factory(request, data, cart)
            if isinstance(reply, dict):
                errors.update(reply)

        # update the cart running the modifiers
        cart.save()

        # add possible form errors for giving feedback to the customer
        response = self.list(request)
        response.data.update(errors=errors)
        return response

    @list_route(methods=['post'], url_path='purchase')
    def purchase(self, request):
        cart = self.get_queryset()
        cart.update(request)
        response = self.list(request)
        # Iterate over the registered modifiers, and search for the active payment service provider
        for modifier in cart_modifiers_pool.get_payment_modifiers():
            if modifier.is_active(cart):
                payment_service_provider = getattr(modifier, 'payment_service', None)
                if payment_service_provider:
                    expression = payment_service_provider.get_payment_request(cart, request)
                    response.data.update(expression=expression)
                break
        return response
