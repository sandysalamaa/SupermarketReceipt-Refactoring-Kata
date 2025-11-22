import unittest

from model_objects import Product, SpecialOfferType, ProductUnit
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


class SupermarketTest(unittest.TestCase):
    """
    BUG FIX VALIDATION: This test was originally FAILING because the ShoppingCart
    silently accepted negative quantities without validation.
    
    EXPECTED: ValueError should be raised when adding negative quantities
    ACTUAL (before fix): No exception was raised, allowing invalid cart state
    ACTUAL (after fix): ValueError is properly raised with descriptive message
    
    This demonstrates the importance of input validation for data integrity.
    """
    def test_negative_quantity(self):
        '''test that negative quantities are handled gracefully '''
        catalog = FakeCatalog()
        product = Product("test", ProductUnit.EACH)  #product instance 
        catalog.add_product(product, 1.0)
        
        cart = ShoppingCart()
        with self.assertRaises(ValueError) as context:
            cart.add_item_quantity(product, -1.0)
        self.assertTrue("Quantity must be positive" in str(context.exception))


    def test_missing_product_in_catalog(self):
        """test behavior when product not in catalog"""
        catalog = FakeCatalog()
        # i'll not run the catalog.add_product(...)
        product = Product("missing product",ProductUnit.EACH)
        cart = ShoppingCart()
        cart.add_item_quantity(product, 1.0)

        teller = Teller(catalog)
        with self.assertRaises(KeyError):
            teller.checks_out_articles_from(cart)
        
    def test_multiple_special_offers_same_product(self):
        """Test scenario where multiple offers might apply to same product"""
        catalog = FakeCatalog()
        product = Product("test", ProductUnit.EACH)
        catalog.add_product(product, 10.0)
        teller = Teller(catalog)
        teller.add_special_offer(SpecialOfferType.TWO_FOR_AMOUNT, product,None)
        teller.add_special_offer(SpecialOfferType.TWO_FOR_AMOUNT, product,15.0)
        
        cart = ShoppingCart()
        cart.add_item_quantity(product, 3)
        receipt = teller.checks_out_articles_from(cart)
        # to verify only one discount is applied
        self.assertEqual(1, len(receipt.discounts))

    def test_zero_quantity_handling(self):
        """Test that zero quantities raise ValueError"""
        catalog = FakeCatalog()
        product = Product("test", ProductUnit.EACH)
        catalog.add_product(product, 1.0)

        cart = ShoppingCart()
        
        with self.assertRaises(ValueError) as context:
            cart.add_item_quantity(product, 0.0)
        
        self.assertIn("Quantity must be positive", str(context.exception))

    def test_ten_percent_discount(self):
        catalog = FakeCatalog()
        toothbrush = Product("toothbrush", ProductUnit.EACH)
        catalog.add_product(toothbrush, 0.99)

        apples = Product("apples", ProductUnit.KILO)
        catalog.add_product(apples, 1.99)

        teller = Teller(catalog)
        teller.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, toothbrush, 10.0)

        cart = ShoppingCart()
        cart.add_item_quantity(apples, 2.5)

        receipt = teller.checks_out_articles_from(cart)

        self.assertAlmostEqual(receipt.total_price(), 4.975, places=2)
        self.assertEqual([], receipt.discounts)
        self.assertEqual(1, len(receipt.items))
        receipt_item = receipt.items[0]
        self.assertEqual(apples, receipt_item.product)
        self.assertEqual(1.99, receipt_item.price)
        self.assertAlmostEqual(receipt_item.total_price, 2.5 * 1.99, places=2)
        self.assertEqual(2.5, receipt_item.quantity)


