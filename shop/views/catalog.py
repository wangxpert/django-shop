# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.cache import add_never_cache_headers
from django.utils.translation import get_language_from_request
from rest_framework import generics
from rest_framework import status
from rest_framework import views
from rest_framework.settings import api_settings
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from shop import settings as shop_settings
from shop.rest.money import JSONRenderer
from shop.rest.filters import CMSPagesFilterBackend
from shop.rest.serializers import AddToCartSerializer, ProductSelectSerializer
from shop.rest.renderers import CMSPageRenderer
from shop.models.product import ProductModel


class ProductListView(generics.ListAPIView):
    """
    This view is used to list all products which shall be visible below a certain URL.
    It normally is added to the urlpatterns as:
    ``url(r'^$', ProductListView.as_view(serializer_class=ProductSummarySerializer))``
    where the ``ProductSummarySerializer`` is a customized REST serializer that that specific
    product model.
    """
    product_model = ProductModel
    serializer_class = None  # must be overridden by ProductListView.as_view
    filter_class = None  # may be overridden by ProductListView.as_view
    limit_choices_to = Q()

    def get(self, request, *args, **kwargs):
        # TODO: we must find a better way to invalidate the cache.
        # Simply adding a no-cache header eventually decreases the performance dramatically.
        response = self.list(request, *args, **kwargs)
        add_never_cache_headers(response)
        return response

    def get_queryset(self):
        qs = self.product_model.objects.filter(self.limit_choices_to)
        # restrict queryset by language
        if hasattr(self.product_model, 'translations'):
            language = get_language_from_request(self.request)
            qs = qs.prefetch_related('translations').filter(translations__language_code=language)
        qs = qs.select_related('polymorphic_ctype')
        return qs

    def get_template_names(self):
        # TODO: let this be configurable through a View member variable
        return [self.request.current_page.get_template()]


class CMSPageProductListView(ProductListView):
    """
    This view is used to list all products being associated with a CMS page. It normally is
    added to the urlpatterns as:
    ``url(r'^$', CMSPageProductListView.as_view(serializer_class=ProductSummarySerializer))``
    where the ``ProductSummarySerializer`` is a customized REST serializer that that specific
    product model.
    """
    renderer_classes = (CMSPageRenderer, JSONRenderer, BrowsableAPIRenderer)
    filter_backends = list(api_settings.DEFAULT_FILTER_BACKENDS)
    filter_backends.append(CMSPagesFilterBackend())

    def filter_queryset(self, queryset):
        self.filter_context = None
        if self.filter_class:
            filter_instance = self.filter_class(self.request.query_params, queryset=queryset)
            if callable(getattr(filter_instance, 'get_render_context', None)):
                self.filter_context = filter_instance.get_render_context()
            elif hasattr(filter_instance, 'render_context'):
                self.filter_context = filter_instance.render_context
        qs = super(CMSPageProductListView, self).filter_queryset(queryset)
        return qs

    def get_renderer_context(self):
        renderer_context = super(CMSPageProductListView, self).get_renderer_context()
        if renderer_context['request'].accepted_renderer.format == 'html':
            renderer_context['filter'] = self.filter_context
        return renderer_context


class SyncCatalogView(views.APIView):
    """
    To be used for synchronizing the catalog list view with the cart.
    Use Angular directive <ANY shop-sync-catalog-item="..."> on each catalog item.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    product_model = ProductModel
    product_field = 'product'
    serializer_class = None  # must be overridden by SyncCatalogView.as_view
    filter_class = None  # may be overridden by SyncCatalogView.as_view
    limit_choices_to = Q()

    def get_context(self, request, **kwargs):
        filter_kwargs = {'id': request.data.get('id')}
        if hasattr(self.product_model, 'translations'):
            filter_kwargs.update(translations__language_code=get_language_from_request(self.request))
        queryset = self.product_model.objects.filter(self.limit_choices_to, **filter_kwargs)
        product = get_object_or_404(queryset)
        return {self.product_field: product, 'request': request}

    def get(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = self.serializer_class(context=context, **kwargs)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = self.serializer_class(data=request.data, context=context)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddToCartView(views.APIView):
    """
    Handle the "Add to Cart" dialog on the products detail page.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    product_model = ProductModel
    serializer_class = AddToCartSerializer
    lookup_field = lookup_url_kwarg = 'slug'
    limit_choices_to = Q()

    def get_context(self, request, **kwargs):
        assert self.lookup_url_kwarg in kwargs
        filter_kwargs = {self.lookup_field: kwargs.pop(self.lookup_url_kwarg)}
        if hasattr(self.product_model, 'translations'):
            filter_kwargs.update(translations__language_code=get_language_from_request(self.request))
        queryset = self.product_model.objects.filter(self.limit_choices_to, **filter_kwargs)
        product = get_object_or_404(queryset)
        return {'product': product, 'request': request}

    def get(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = self.serializer_class(context=context, **kwargs)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        context = self.get_context(request, **kwargs)
        serializer = self.serializer_class(data=request.data, context=context)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductRetrieveView(generics.RetrieveAPIView):
    """
    View responsible for rendering the products details.
    """
    renderer_classes = (CMSPageRenderer, JSONRenderer, BrowsableAPIRenderer)
    lookup_field = lookup_url_kwarg = 'slug'
    product_model = ProductModel
    serializer_class = None  # must be overridden by ProductListView.as_view
    limit_choices_to = Q()

    def get_template_names(self):
        product = self.get_object()
        app_label = product._meta.app_label.lower()
        basename = '{}-detail.html'.format(product.__class__.__name__.lower())
        return [
            os.path.join(app_label, 'catalog', basename),
            os.path.join(app_label, 'catalog/product-detail.html'),
            'shop/catalog/product-detail.html',
        ]

    def get_renderer_context(self):
        renderer_context = super(ProductRetrieveView, self).get_renderer_context()
        if renderer_context['request'].accepted_renderer.format == 'html':
            # add the product as Python object to the context
            renderer_context['product'] = self.get_object()
            renderer_context['ng_model_options'] = shop_settings.ADD2CART_NG_MODEL_OPTIONS
        return renderer_context

    def get_object(self):
        if not hasattr(self, '_product'):
            assert self.lookup_url_kwarg in self.kwargs
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
            if hasattr(self.product_model, 'translations'):
                filter_kwargs.update(translations__language_code=get_language_from_request(self.request))
            queryset = self.product_model.objects.filter(self.limit_choices_to, **filter_kwargs)
            self._product = get_object_or_404(queryset)
        return self._product


class ProductSelectView(generics.ListAPIView):
    """
    A simple list view, which is used only by the admin backend. It is required to fetch
    the data for rendering the select widget when looking up for a product.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = ProductSelectSerializer

    def get_queryset(self):
        term = self.request.GET.get('term', '')
        if len(term) >= 2:
            return ProductModel.objects.select_lookup(term)[:10]
        return ProductModel.objects.all()[:10]
