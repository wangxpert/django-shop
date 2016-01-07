# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.six.moves.urllib.parse import urljoin
from djangocms_text_ckeditor.fields import HTMLField
from parler.models import TranslatableModel, TranslatedFieldsModel
from parler.fields import TranslatedField
from parler.managers import TranslatableManager, TranslatableQuerySet
from polymorphic.query import PolymorphicQuerySet
from shop.models.product import BaseProductManager
from shop.models.product import BaseProduct
from myshop.models.properties import Manufacturer, ProductPage, ProductImage


class ProductQuerySet(TranslatableQuerySet, PolymorphicQuerySet):
    pass


class ProductManager(BaseProductManager, TranslatableManager):
    queryset_class = ProductQuerySet

    def select_lookup(self, term):
        query = models.Q(name__icontains=term) | models.Q(slug__icontains=term)
        return self.get_queryset().filter(query)


class Product(BaseProduct, TranslatableModel):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    slug = models.SlugField(verbose_name=_("Slug"), unique=True)
    description = TranslatedField()

    # common product properties
    manufacturer = models.ForeignKey(Manufacturer, verbose_name=_("Manufacturer"))

    # controlling the catalog
    order = models.PositiveIntegerField(verbose_name=_("Sort by"), db_index=True)
    cms_pages = models.ManyToManyField('cms.Page', through=ProductPage,
        help_text=_("Choose list view this product shall appear on."))
    images = models.ManyToManyField('filer.Image', through=ProductImage)

    class Meta:
        ordering = ('order',)

    objects = ProductManager()

    # filter expression used to search for a product item using the Select2 widget
    search_fields = ('identifier__istartswith', 'translations__name__istartswith',)

    def get_absolute_url(self):
        # sorting by highest level, so that the canonical URL associates with the most generic category
        cms_page = self.cms_pages.order_by('depth').last()
        if cms_page is None:
            return urljoin('category-not-assigned', self.slug)
        return urljoin(cms_page.get_absolute_url(), self.slug)

    @property
    def product_name(self):
        return self.name

    @property
    def sample_image(self):
        return self.images.first()

    def get_product_markedness(self, extra):
        """
        Get the markedness of a product.
        Raises `Product.objects.DoesNotExists` if there is no markedness for the given `extra`.
        """
        msg = "Method get_product_markedness(extra) must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))


class ProductTranslation(TranslatedFieldsModel):
    master = models.ForeignKey(Product, related_name='translations', null=True)
    description = HTMLField(verbose_name=_("Description"),
                            help_text=_("Description for the list view of products."))

    class Meta:
        unique_together = [('language_code', 'master')]
