from model_objects import Offer
from receipt import Receipt


class Teller:

    def __init__(self, catalog):
        self.catalog = catalog
        self.offers: dict = {}
        
        # OLD CODE
        # self.catalog = catalog
        # self.offers = {}

        # def add_special_offer(self, offer_type, product, argument):
        #     self.offers[product] = Offer(offer_type, product, argument)

    def product_with_name(self, name):
        """
        NEW METHOD: Find product by name in catalog
        Used by texttest_feature.py to lookup products from CSV files
        
        Args:
            name: Product name to search for
            
        Returns:
            Product object if found
            
        Raises:
            ValueError: If product not found in catalog
        """
        # check if catalog has a products dictionary (FakeCatalog)
        if hasattr(self.catalog, 'products'):
            for product in self.catalog.products.values():
                if product.name == name:
                    return product
        # alternative: if we need to search differently for other catalog types
        else:
            # This would need to be implemented based on actual catalog structure
            raise NotImplementedError("Product lookup not implemented for this catalog type")
        
        raise ValueError(f"Product '{name}' not found in catalog")

    def add_special_offer(self, offer_type, product, argument):
        if product is None:
            raise ValueError("product cannot be None")
        if argument is None:
            raise ValueError("offer argument cannot be None")
        self.offers[product] = Offer(offer_type, product, argument)


    def checks_out_articles_from(self, the_cart):
        receipt = Receipt()
        product_quantities = the_cart.items
        for pq in product_quantities:
            p = pq.product
            quantity = pq.quantity
            unit_price = self.catalog.unit_price(p)
            price = quantity * unit_price
            receipt.add_product(p, quantity, unit_price, price)

        the_cart.handle_offers(receipt, self.offers, self.catalog)

        return receipt
