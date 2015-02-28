# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import itertools
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import select_template
from rest_framework import serializers
from rest_framework import generics
from rest_framework import status
from rest_framework import views
from rest_framework.fields import empty
from rest_framework.renderers import TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from shop.money.rest import JSONRenderer, MoneyField
from shop.models.product import BaseProduct


class ProductSerializerBase(serializers.ModelSerializer):
    """
    Common serializer for the Product model, both for the ProductSummarySerializer and the
    ProductDetailSerializer.
    """
    price = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = getattr(BaseProduct, 'MaterializedModel')
        fields = ('name', 'identifier', 'price', 'availability')

    def get_price(self, product):
        return product.get_price(self.context['request'])

    def get_availability(self, product):
        return product.get_availability(self.context['request'])


class ProductSummarySerializer(ProductSerializerBase):
    """
    Serialize a subset of the Product model, suitable for list views, cart- and order-lists.
    """
    product_url = serializers.CharField(source='get_absolute_url', read_only=True)
    html = serializers.SerializerMethodField()

    class Meta(ProductSerializerBase.Meta):
        fields = ProductSerializerBase.Meta.fields + ('product_url', 'html') \
            + getattr(ProductSerializerBase.Meta.model, 'summary_fields', ())

    def find_template(self, product):
        app_label = product._meta.app_label.lower()
        basename = '{}-summary.html'.format(product.__class__.__name__.lower())
        prefix = self.context.get('serializer_name')
        templates = [(app_label, basename), (app_label, 'product-summary.html'), ('shop', 'product-summary.html')]
        if prefix:
            prefixed_templates = [(base, prefix + '-' + leaf) for base, leaf in templates]
            templates = itertools.chain.from_iterable(zip(prefixed_templates, templates))
        templates = [os.path.join(base, leaf) for base, leaf in templates]
        return select_template(templates)

    def get_html(self, product):
        """
        Return a HTML snippet containing a rendered summary for this product.
        """
        template = self.find_template(product)
        request = self.context['request']
        context = RequestContext(request, {'product': product})
        return template.render(context)


class ProductDetailSerializer(ProductSerializerBase):
    """
    Serialize all fields of the Product model, for the products detail view.
    """
    class Meta(ProductSerializerBase.Meta):
        exclude = ()


class ProductRetrieveView(generics.RetrieveAPIView):
    """
    View responsible for rendering the products details.
    Additionally an extra method as shown in products lists, cart lists
    and order item lists.
    """
    serializer_class = ProductDetailSerializer
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)

    def get_template_names(self):
        app_label = self.product._meta.app_label.lower()
        basename = '{}-detail.html'.format(self.product.__class__.__name__.lower())
        return [
            os.path.join(app_label, basename),
            os.path.join(app_label, 'product-detail.html'),
            'shop/product-detail.html',
        ]

    def get_renderer_context(self):
        context = super(ProductRetrieveView, self).get_renderer_context()
        # if the used renderer is a `TemplateHTMLRenderer`, then enrich the
        # context with some unserializable Python objects
        if context['request'].accepted_renderer.format == 'html':
            context['request'].passo = 'passo'  # TODO: add what we need here
        return context

    def get_object(self):
        assert self.lookup_url_kwarg in self.kwargs
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
        queryset = getattr(BaseProduct, 'MaterializedModel').objects
        queryset = queryset.filter(self.limit_choices_to, **filter_kwargs)
        product = get_object_or_404(queryset)
        self.product = product
        return product

    def get(self, request, *args, **kwargs):
        self.limit_choices_to = kwargs.pop('limit_choices_to')
        self.lookup_url_kwarg = kwargs.pop('lookup_url_kwarg')
        self.lookup_field = kwargs.pop('lookup_field')
        return self.retrieve(request, *args, **kwargs)


class AddToCartSerializer(serializers.Serializer):
    """
    Serialize fields used in the "Add to Cart" dialog box.
    """
    quantity = serializers.IntegerField(default=1, min_value=1)
    unit_price = MoneyField(read_only=True)
    subtotal = MoneyField(read_only=True)
    product = serializers.IntegerField(read_only=True, help_text="The product's primary key")

    def __init__(self, data=empty, **kwargs):
        context = kwargs.get('context', {})
        if 'product' not in context or 'request' not in context:
            raise ValueError("A context is required for this serializer and must contain the `product` and the `request` object.")
        instance = {'product': context['product'].id}
        unit_price = context['product'].get_price(context['request'])
        if data == empty:
            quantity = self.fields['quantity'].default
        else:
            quantity = data['quantity']
        instance.update(quantity=quantity, unit_price=unit_price, subtotal=quantity * unit_price)
        super(AddToCartSerializer, self).__init__(instance, data, **kwargs)

    def validate_quantity(self, data):
        return data


class AddToCartView(views.APIView):
    """
    Handle the "Add to Cart" dialog on the products detail page.
    """
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)
    lookup_field = lookup_url_kwarg = 'slug'
    limit_choices_to = Q()

    def get_context(self, request, **kwargs):
        assert self.lookup_url_kwarg in kwargs
        filter_kwargs = {self.lookup_field: kwargs.pop(self.lookup_url_kwarg)}
        queryset = getattr(BaseProduct, 'MaterializedModel').objects
        queryset = queryset.filter(self.limit_choices_to, **filter_kwargs)
        product = get_object_or_404(queryset)
        return {'product': product, 'request': request}

    def get_template_names(self):
        # TODO: more templates
        return ['shop/product-add2cart.html']

    def get(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = AddToCartSerializer(context=context)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = AddToCartSerializer(data=request.data, context=context)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSummarySerializer
    renderer_classes = (TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer)
    limit_choices_to = Q()
    template_name = 'shop/products-list.html'

    def get_queryset(self):
        qs = getattr(BaseProduct, 'MaterializedModel').objects.filter(self.limit_choices_to)

        # restrict products for current CMS page
        current_page = self.request._request.current_page
        if current_page.publisher_is_draft:
            current_page = current_page.publisher_public
        qs = qs.filter(cms_pages=current_page)
        return qs

    def paginate_queryset(self, queryset):
        page = super(ProductListView, self).paginate_queryset(queryset)
        self.paginator = page.paginator
        return page

    def get_renderer_context(self):
        context = super(ProductListView, self).get_renderer_context()
        # The RESTframework does not add the paginator to the rendering context
        context['request'].paginator = self.paginator
        return context
