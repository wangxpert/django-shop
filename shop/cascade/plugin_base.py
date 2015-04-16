# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _
from django.utils.module_loading import import_by_path
from cms.plugin_pool import plugin_pool
from cmsplugin_cascade.fields import PartialFormField
from cmsplugin_cascade.plugin_base import CascadePluginBase


class ShopPluginBase(CascadePluginBase):
    module = 'Shop'
    require_parent = False
    allow_children = False


class DialogFormPlugin(ShopPluginBase):
    """
    Base class for all plugins adding a dialog form to a placeholder field.
    """
    require_parent = True
    parent_classes = ('BootstrapColumnPlugin',)
    CHOICES = (('form', _("Form dialog")), ('summary', _("Summary")),)
    glossary_fields = (
        PartialFormField('render_type',
            widgets.RadioSelect(choices=CHOICES),
            label=_("Render as"),
            initial='form',
            help_text=_("A dialog can also be rendered as a box containing a read-only summary."),
        ),
        PartialFormField('stop_on_error',
            widgets.CheckboxInput(),
            label=_("Stop on error"),
            initial=False,
            help_text=_("Activate, if processing shall stop immediately on invalid form data."),
        ),
    )

    @classmethod
    def register_plugin(cls, plugin):
        """
        Register plugins derived from this class with this function instead of
        `plugin_pool.register_plugin`, so that dialog plugins without a corresponding
        form class are not registered.
        """
        if not issubclass(plugin, cls):
            msg = "Can not register plugin class `{}`, since is does not inherit from `{}`."
            raise ImproperlyConfigured(msg.format(plugin.__name__, cls.__name__))
        if not getattr(plugin, 'form_class', None):
            msg = "Can not register plugin class `{}`, since is does not define a `form_class`."
            raise ImproperlyConfigured(msg.format(plugin.__name__))
        plugin_pool.register_plugin(plugin)

    def __init__(self, *args, **kwargs):
        super(DialogFormPlugin, self).__init__(*args, **kwargs)
        self.FormClass = import_by_path(self.form_class)

    def get_form_data(self, request):
        """
        Returns data to initialize the corresponding dialog form.
        This method must return a dictionary containing either `instance` - a Python object to
        initialize the form class for this plugin, or `initial` - a dictionary containing initial
        form data, or both.
        """
        return {}

    def render(self, context, instance, placeholder):
        request = context['request']
        form_data = self.get_form_data(request)
        request._plugin_order = getattr(request, '_plugin_order', 0) + 1
        initial = form_data.pop('initial', {})
        initial.update(plugin_id=instance.id, plugin_order=request._plugin_order)
        context[self.FormClass.form_name] = self.FormClass(initial=initial, **form_data)
        return super(DialogFormPlugin, self).render(context, instance, placeholder)
