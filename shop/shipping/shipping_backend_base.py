# -*- coding: utf-8 -*-

class BaseShippingBackend():
    
    def process_order(self,order):
        '''
        Processes the supplied Order object for shipping costs computing.
        This should ideally store the shipping costs total in 
        Order.shipping_cost.
        
        '''
        
    def process_order_item(self,order_item):
        '''
        Processes the supplied Order object for shipping costs computing.
        This should ideally store the shipping costs total in 
        Order.shipping_cost.
        
        '''