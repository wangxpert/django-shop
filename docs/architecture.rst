.. _architecture:

=====================
Software Architecture
=====================

The **djangoSHOP** framework is, as its name implies, a framework and not a software which runs
out of the box. Instead an e-commerce site built upon **djangoSHOP**, always consists of this
framework, a bunch of other Django apps and the merchant's own implementation. While this may seem
more complicate than a ready-to-use solution, it gives the programmer enormous advantages during the
implementation.


Feature Completeness
====================

A merchant who wants to implement a unique feature for his e-commerce site, **must** never have to
touch the code of the framework. Aiming for feature completeness means, that no matter how
challenging a feature is, it must be possible to be implemented into the merchant's implementation,
rather than by patching the framework.


Core System
===========

Generally, the shop system can be seen in three different phases:


The shopping phase
------------------

From a customers perspective, this is where we look around at different products, presumably in
different categories. We denote this as the catalog list- and catalog detail views. Here we browse,
search and filter for products. In one of the list views, we edit the quantity of the products to
be added to our shopping cart.

Each time a product is added, the cart is updated which in turn run the so named "Cart Modifiers".
Cart modifiers sum up the line totals, add taxes, rebates and shipping costs to compute the final
total. The Cart Modifiers are also during the checkout phase (see below), since the chosen shipping
method and destination, as well as the payment method may modify the final total.


The checkout process
--------------------

Her the customer must be able to refine the cart' content: Change the quantity of an item, or remove
that item completely from the cart.

During the checkout process, the customer must enter his addresses and payment informations. These
settings may also influence the cart's total.

The final step during checkout is the purchase operation. This is where the cart's content is
converted into an order object and emptied afterwards.


The fulfillment phase
---------------------

It is now the merchants's turn to take further steps. Depending on the order status, certain
actions must be performed immediately or the order must be kept in the current state until some
external events happen. This could be a payment receivement, or that an ordered item arrived in
stock. While setting up a **djangoSHOP** project, the allowed status transitions for the fulfillment
phase can be plugged together, giving the merchant the possibility to programmatically define his
order workflows.


Plugins
=======

Django SHOP defines 5 types of different plugins:

1. Product models
2. Cart modifiers
3. Payment backends
4. Shipping backends
4. Order workflow modules

They may be added as a third party **djangoSHOP** plugin, or integrated into the merchant's
implementation.
