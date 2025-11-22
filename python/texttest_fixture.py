"""
Start texttest from a command prompt in the same folder as this file with this command:

texttest -a sr -d .
"""

import sys, csv
from pathlib import Path

from model_objects import Product, SpecialOfferType, ProductUnit
from receipt_printer import ReceiptPrinter
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def read_catalog(catalog_file):
    """
    ENHANCED: Read products from CSV file with comprehensive error handling
    Previously had no error handling - could crash on invalid data
    """
    catalog = FakeCatalog()
    
    if not catalog_file.exists():
        print(f"Warning: {catalog_file} not found, using empty catalog")
        return catalog
    
    try:
        with open(catalog_file, "r", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 2):  # start from line 2 (header is line 1)
                try:
                    # Validate required fields
                    if 'name' not in row or not row['name'].strip():
                        print(f"Warning: Missing product name in line {row_num}, skipping")
                        continue
                    
                    if 'unit' not in row:
                        print(f"Warning: Missing unit in line {row_num} for product '{row['name']}', skipping")
                        continue
                    
                    if 'price' not in row:
                        print(f"Warning: Missing price in line {row_num} for product '{row['name']}', skipping")
                        continue
                    
                    name = row['name'].strip()
                    unit_str = row['unit'].strip().upper()
                    price_str = row['price'].strip()
                    
                    # Validate and convert unit
                    try:
                        unit = ProductUnit[unit_str]
                    except KeyError:
                        print(f"Warning: Invalid unit '{unit_str}' for product '{name}' in line {row_num}. Must be EACH or KILO. Skipping.")
                        continue
                    
                    # Validate and convert price
                    try:
                        price = float(price_str)
                        if price < 0:
                            print(f"Warning: Negative price {price} for product '{name}' in line {row_num}. Skipping.")
                            continue
                        if price > 100000:  # Reasonable upper limit
                            print(f"Warning: Unrealistically high price {price} for product '{name}' in line {row_num}. Skipping.")
                            continue
                    except ValueError:
                        print(f"Warning: Invalid price '{price_str}' for product '{name}' in line {row_num}. Skipping.")
                        continue
                    
                    # Create and add product
                    product = Product(name, unit)
                    catalog.add_product(product, price)
                    print(f"Added product: {name} - {unit_str} - ${price:.2f}")
                    
                except (KeyError, ValueError) as e:
                    print(f"Error processing line {row_num} in {catalog_file}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Failed to read {catalog_file}: {e}")
    
    print(f"Catalog loaded with {len(catalog.products)} products")
    return catalog


def read_offers(offers_file, teller):
    """
    ENHANCED: Read special offers from CSV file with error handling
    """
    if not offers_file.exists():
        print(f"Info: {offers_file} not found, no special offers loaded")
        return
    
    offers_loaded = 0
    try:
        with open(offers_file, "r", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 2):
                try:
                    # Validate required fields
                    if 'name' not in row or not row['name'].strip():
                        print(f"Warning: Missing product name in offers line {row_num}, skipping")
                        continue
                    
                    if 'offer' not in row:
                        print(f"Warning: Missing offer type in line {row_num}, skipping")
                        continue
                    
                    name = row['name'].strip()
                    offer_str = row['offer'].strip().upper()
                    
                    # Lookup product
                    try:
                        product = teller.product_with_name(name)
                    except ValueError as e:
                        print(f"Warning: {e} in offers line {row_num}. Skipping.")
                        continue
                    
                    # Validate offer type
                    try:
                        offer_type = SpecialOfferType[offer_str]
                    except KeyError:
                        valid_offers = [e.name for e in SpecialOfferType]
                        print(f"Warning: Invalid offer type '{offer_str}' in line {row_num}. Must be one of {valid_offers}. Skipping.")
                        continue
                    
                    # Handle argument (optional for some offer types)
                    argument = 0.0
                    if 'argument' in row and row['argument'].strip():
                        try:
                            argument = float(row['argument'].strip())
                        except ValueError:
                            print(f"Warning: Invalid argument '{row['argument']}' in line {row_num}. Using 0.0.")
                    
                    # Add the offer
                    teller.add_special_offer(offer_type, product, argument)
                    offers_loaded += 1
                    print(f"Added offer: {name} - {offer_str} - {argument}")
                    
                except Exception as e:
                    print(f"Error processing offers line {row_num}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Failed to read {offers_file}: {e}")
    
    print(f"Loaded {offers_loaded} special offers")


def read_basket(cart_file, catalog):
    """
    ENHANCED: Read shopping basket from CSV file with error handling
    """
    cart = ShoppingCart()
    
    if not cart_file.exists():
        print(f"Info: {cart_file} not found, using empty cart")
        return cart
    
    items_loaded = 0
    try:
        with open(cart_file, "r", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 2):
                try:
                    # Validate required fields
                    if 'name' not in row or not row['name'].strip():
                        print(f"Warning: Missing product name in cart line {row_num}, skipping")
                        continue
                    
                    if 'quantity' not in row:
                        print(f"Warning: Missing quantity in line {row_num}, skipping")
                        continue
                    
                    name = row['name'].strip()
                    quantity_str = row['quantity'].strip()
                    
                    # Lookup product in catalog
                    if name not in catalog.products:
                        print(f"Warning: Product '{name}' not found in catalog (cart line {row_num}). Skipping.")
                        continue
                    
                    product = catalog.products[name]
                    
                    # Validate and convert quantity
                    try:
                        quantity = float(quantity_str)
                        if quantity <= 0:
                            print(f"Warning: Non-positive quantity {quantity} for product '{name}' in line {row_num}. Skipping.")
                            continue
                        if quantity > 1000:  # Reasonable upper limit
                            print(f"Warning: Unrealistically high quantity {quantity} for product '{name}' in line {row_num}. Skipping.")
                            continue
                    except ValueError:
                        print(f"Warning: Invalid quantity '{quantity_str}' for product '{name}' in line {row_num}. Skipping.")
                        continue
                    
                    # Add to cart
                    cart.add_item_quantity(product, quantity)
                    items_loaded += 1
                    print(f"Added to cart: {name} - {quantity}")
                    
                except Exception as e:
                    print(f"Error processing cart line {row_num}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Failed to read {cart_file}: {e}")
    
    print(f"Cart loaded with {items_loaded} items")
    return cart


def main(args):
    """
    ENHANCED: Main function with better error handling and user feedback
    """
    print("=== Supermarket Receipt System ===")
    print("Loading catalog, offers, and cart...")
    
    try:
        # Read all data files
        catalog = read_catalog(Path("catalog.csv"))
        teller = Teller(catalog)
        read_offers(Path("offers.csv"), teller)
        basket = read_basket(Path("cart.csv"), catalog)
        
        # Check if cart is empty
        if not basket.items:
            print("Warning: Shopping cart is empty!")
            return
        
        # Process checkout
        print("\nProcessing checkout...")
        receipt = teller.checks_out_articles_from(basket)
        
        # Print receipt
        print("\n" + "="*50)
        print(ReceiptPrinter().print_receipt(receipt))
        print("="*50)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])