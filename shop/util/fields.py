# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db.models.fields import DecimalField


class CurrencyField(DecimalField):
    """
    A CurrencyField is simply a subclass of DecimalField with a fixed format:
    max_digits = 12, decimal_places=2, and defaults to 0.00
    """
    def __init__(self, **kwargs):
        if 'max_digits' in kwargs.keys():
            del kwargs['max_digits']
        if 'decimal_places' in kwargs.keys():
            del kwargs['decimal_places']
        default = kwargs.get('default', Decimal('0.00')) # get "default" or 0.00
        if 'default' in kwargs.keys():
            del kwargs['default']
        return super(CurrencyField,self).__init__(max_digits=12,decimal_places=2,default=default,**kwargs)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.DecimalField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
