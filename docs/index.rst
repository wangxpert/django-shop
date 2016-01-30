
=========================
Django SHOP documentation
=========================

This is the documentation starting from version 0.9; if you are looking for the documentation of
django-shop version 0.2, please check the sidebar of RTD.

Version 0.9 of **djangoSHOP** is a complete rewrite of the code base, keeping the concepts of model
overriding and cart modifiers. With some effort it should be possible to migrate existing projects
to this new release.


Tutorial
========

This tutorial shows how to setup a working e-commerce site with **djangoSHOP** using the given
dependencies. The code required to setup this demo can be found in the example/myshop folder.

.. toctree::
	:maxdepth: 1
	:numbered:

	tutorial/intro
	tutorial/quickstart
	tutorial/simple-product
	tutorial/multilingual-product
	tutorial/polymorphic-product
	tutorial/catalog-views
	tutorial/cart-checkout


Reference
==========

Reference to classes and concepts used in **djangoSHOP**

.. toctree::
	:maxdepth: 1
	:numbered:

	reference/customer-model
	reference/deferred-models
	reference/money-types
	reference/product-models
	reference/catalog
	reference/cascade-plugins
	reference/cart-checkout
	reference/payment-providers
	reference/order
	reference/search
	reference/notifications
	reference/serializers


Development and Community
=========================

.. toctree::
	:maxdepth: 1

	contributing
