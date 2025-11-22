import math

from model_objects import ProductQuantity, SpecialOfferType, Discount


class ShoppingCart:

    def __init__(self):
        self._items = []
        self._product_quantities = {} # key: Product, value: quantity

    @property
    def items(self):
        return self._items

    def add_item(self, product):
        self.add_item_quantity(product, 1.0)

    @property
    def product_quantities(self):
        return self._product_quantities

    def add_item_quantity(self, product, quantity):
    # INPUT VALIDATION ADDED - Previously, negative quantities were silently accepted
    # which could lead to invalid cart states and incorrect pricing calculations.
    # Test 'test_negative_quantity_handling' was failing because no ValueError was raised.
    # Now we properly validate inputs to maintain data integrity.
        if quantity <= 0:
            raise ValueError("Quantity must be positive")    
        if product is None:
            raise ValueError("please provide a valid product")
        
        self._items.append(ProductQuantity(product, quantity))
        if product in self._product_quantities.keys():
            self._product_quantities[product] = self._product_quantities[product] + quantity
        else:
            self._product_quantities[product] = quantity

    def handle_offers(self, receipt, offers, catalog):
        """
        REFACTORED: Main method to handle all special offers for products in cart.
        Previously was a 40+ line complex method with nested conditionals.
        
        Now it simply:
        1. Iterates through all products in cart
        2. Checks if product has any special offers
        3. Delegates discount calculation to specialized methods
        4. Adds valid discounts to receipt
        
        This follows Single Responsibility Principle - this method only coordinates,
        while calculation logic is separated into focused methods.
        """
        discount = None
        for product , quantity in self._product_quantities.items():
            if product in offers:
                offer = offers[product]
                discount = self._calculate_discount(product, quantity, offer, catalog)
            if discount:
                receipt.add_discount(discount)
    
    def _calculate_discount(self, product, quantity, offer, catalog):
        """
        REFACTORED: Central discount calculation router.
        Replaces complex nested if-else logic from original handle_offers method.
        
        Determines the offer type and delegates to appropriate calculation method.
        This makes it easy to add new discount types without modifying existing logic.
        
        Args:
            product: The product to calculate discount for
            quantity: Quantity of the product in cart
            offer: The special offer details
            catalog: Catalog for price lookups
        
        Returns:
            Discount object if applicable, None otherwise
        """
        unit_price = catalog.unit_price(product)
        quantity_as_int = int(quantity)

        if offer.offer_type == SpecialOfferType.THREE_FOR_TWO:
            return self._calculate_three_for_two_discount(product, quantity_as_int, unit_price)
        elif offer.offer_type == SpecialOfferType.TWO_FOR_AMOUNT:
            return self._calculate_two_for_amount_discount(product, quantity_as_int, unit_price, offer.argument)
        elif offer.offer_type == SpecialOfferType.FIVE_FOR_AMOUNT:
            return self._calculate_five_for_amount_discount(product, quantity_as_int, unit_price, offer.argument)
        elif offer.offer_type == SpecialOfferType.TEN_PERCENT_DISCOUNT:
            return self._calculate_percentage_discount(product, quantity, unit_price, offer.argument)
        
        return None
    
    def _calculate_percentage_discount(self, product, quantity, unit_price, percentage):
        """
        calculates percentage discount on the total price of a product.
        
        Example:
        - Product price: $10.0, Quantity: 2, Discount: 10%
        - Total before discount: 2 * $10.0 = $20.0
        - Discount amount: $20.0 * 10% = $2.0
        - Discount object: -$2.0
        
        Args:
            product: Product getting discount
            quantity: Quantity of product (can be decimal for weight products)
            unit_price: Price per unit from catalog
            percentage: Discount percentage (e.g., 10.0 for 10% off)
        
        Returns:
            Discount object with calculated amount, or None if no discount applies
        """
        if percentage > 0:
            discount_amount = quantity * unit_price * percentage / 100.0
            return Discount(product, f"{percentage}% off", -discount_amount)
        return None

    def _calculate_three_for_two_discount(self, product, quantity, unit_price):
        """
        Calculates '3 for 2' discount: Buy 3 items, pay for 2.
        
        Example: 
        - Quantity: 3 → discount = 1 * unit_price
        - Quantity: 6 → discount = 2 * unit_price
        - Quantity: 2 → no discount
        
        Args:
            product: Product getting discount
            quantity: Integer quantity of product
            unit_price: Price per unit from catalog
        
        Returns:
            Discount object with calculated amount, or None if no discount applies
        """
        if quantity > 2:
            number_of_threes = quantity // 3
            discount_amount = number_of_threes * unit_price
            return Discount(product, "3 for 2", -discount_amount)
        return None
    
    def get_cart_summary(self):
        """
        ENHANCEMENT: Provides quick cart summary.
        """
        total_items = len(self._items)
        total_products = len(self._product_quantities)
        total_quantity = sum(self._product_quantities.values())
        
        return {
            'total_items': total_items,
            'total_products': total_products,
            'total_quantity': total_quantity
        }
    
    def get_cross_sell_recommendations(self, catalog, product_associations):
        """
        AMAZON-STYLE: "Customers who bought this also bought..."
        """
        recommendations = set()
        
        for product in self._product_quantities:
            if product.name in product_associations:   #product_associations is a dict of related products can be bought
                for associated_product in product_associations[product.name]:
                    if associated_product not in self._product_quantities:
                        recommendations.add(associated_product)
        
        return list(recommendations)[:3]  # top 3 recommendations

    # OLD CODE
    # def handle_offers(self, receipt, offers, catalog):
  
        # for p in self._product_quantities.keys():
        #     quantity = self._product_quantities[p]
        #     if p in offers.keys():
        #         offer = offers[p]
        #         unit_price = catalog.unit_price(p)
        #         quantity_as_int = int(quantity)
        #         discount = None
        #         x = 1
        #         if offer.offer_type == SpecialOfferType.THREE_FOR_TWO:
        #             x = 3

        #         elif offer.offer_type == SpecialOfferType.TWO_FOR_AMOUNT:
        #             x = 2
        #             if quantity_as_int >= 2:

        #                 total = offer.argument * (quantity_as_int / x) + quantity_as_int % 2 * unit_price
        #                 discount_n = unit_price * quantity - total
        #                 discount = Discount(p, "2 for " + str(offer.argument), -discount_n)

        #         if offer.offer_type == SpecialOfferType.FIVE_FOR_AMOUNT:
        #             x = 5

        #         number_of_x = math.floor(quantity_as_int / x)
        #         if offer.offer_type == SpecialOfferType.THREE_FOR_TWO and quantity_as_int > 2:
        #             discount_amount = quantity * unit_price - (
        #                         (number_of_x * 2 * unit_price) + quantity_as_int % 3 * unit_price)
        #             discount = Discount(p, "3 for 2", -discount_amount)

        #         if offer.offer_type == SpecialOfferType.TEN_PERCENT_DISCOUNT:
        #             discount = Discount(p, str(offer.argument) + "% off",
        #                                 -quantity * unit_price * offer.argument / 100.0)

        #         if offer.offer_type == SpecialOfferType.FIVE_FOR_AMOUNT and quantity_as_int >= 5:
        #             discount_total = unit_price * quantity - (
        #                         offer.argument * number_of_x + quantity_as_int % 5 * unit_price)
        #             discount = Discount(p, str(x) + " for " + str(offer.argument), -discount_total)

        #         if discount:
        #             receipt.add_discount(discount)
