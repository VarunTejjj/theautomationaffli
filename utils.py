# utils.py

import json
import os

PRODUCTS_FILE = "products.json"

def load_products():
    """Load all products from JSON DB."""
    if not os.path.isfile(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w") as f:
            json.dump({}, f)
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    """Save products dict to file."""
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

def get_next_product_id(products):
    """Generate the next product id as string."""
    if products:
        last_id = max(int(pid) for pid in products)
        return str(last_id + 1)
    return "10001"
