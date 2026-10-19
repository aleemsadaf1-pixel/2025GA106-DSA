import threading
import json
import os
import random
import time


CATEGORIES = [
    "Electronics", "Clothing", "Home & Kitchen", "Sports", "Books",
    "Toys", "Beauty", "Automotive", "Garden", "Food",
    "Health", "Office", "Pet Supplies", "Baby", "Tools",
]

BRANDS = [
    "TechPro", "StyleMax", "HomeEase", "SportFit", "ReadMore",
    "FunPlay", "GlowUp", "AutoParts", "GreenThumb", "TastyBite",
    "WellLife", "DeskMate", "PetJoy", "BabyComfort", "ToolMaster",
    "NovaTech", "UrbanWear", "CozyHome", "ActiveGear", "PageTurner",
    "SmartChoice", "PureBeauty", "RoadReady", "EcoGrow", "FreshBite",
]

ADJECTIVES = [
    "Premium", "Ultra", "Pro", "Deluxe", "Classic", "Modern",
    "Slim", "Smart", "Eco", "Turbo", "Mini", "Max", "Elite",
    "Basic", "Advanced", "Compact", "Wireless", "Portable",
    "Heavy-Duty", "Lightweight",
]

PRODUCT_TYPES = {
    "Electronics":    ["Headphones", "Speaker", "Charger", "Cable", "Mouse",
                       "Keyboard", "Monitor", "Webcam", "USB Hub", "Laptop Stand"],
    "Clothing":       ["T-Shirt", "Jeans", "Jacket", "Hoodie", "Sneakers",
                       "Socks", "Cap", "Belt", "Scarf", "Gloves"],
    "Home & Kitchen": ["Blender", "Toaster", "Lamp", "Rug", "Curtain",
                       "Pan", "Knife Set", "Mug", "Plate Set", "Towel"],
    "Sports":         ["Yoga Mat", "Dumbbell", "Water Bottle", "Resistance Band",
                       "Jump Rope", "Helmet", "Shin Guard", "Gloves", "Ball", "Bag"],
    "Books":          ["Novel", "Textbook", "Guide", "Cookbook", "Journal",
                       "Planner", "Notebook", "Dictionary", "Atlas", "Manual"],
    "Toys":           ["Action Figure", "Puzzle", "Board Game", "Doll", "Car",
                       "Building Set", "Stuffed Animal", "Kite", "Craft Kit", "Robot"],
    "Beauty":         ["Moisturizer", "Lipstick", "Foundation", "Serum", "Face Mask",
                       "Shampoo", "Conditioner", "Perfume", "Sunscreen", "Brush"],
    "Automotive":     ["Floor Mat", "Phone Mount", "Air Freshener", "Seat Cover",
                       "Dash Cam", "Jump Starter", "Tool Kit", "Car Wax", "Polish", "LED Light"],
    "Garden":         ["Plant Pot", "Shovel", "Hose", "Fertilizer", "Seeds",
                       "Pruner", "Sprinkler", "Garden Gloves", "Rake", "Wheelbarrow"],
    "Food":           ["Chocolate", "Coffee", "Tea", "Snack Bar", "Protein Powder",
                       "Honey", "Olive Oil", "Spice Set", "Sauce", "Dried Fruit"],
    "Health":         ["Vitamins", "First Aid Kit", "Thermometer", "Bandage", "Supplement",
                       "Face Mask", "Sanitizer", "Ice Pack", "Pillow", "Brace"],
    "Office":         ["Pen Set", "Stapler", "Folder", "Desk Organizer", "Tape",
                       "Paper", "Marker", "Clipboard", "Calculator", "Label Maker"],
    "Pet Supplies":   ["Dog Food", "Cat Toy", "Leash", "Pet Bed", "Bowl",
                       "Pet Shampoo", "Collar", "Treat", "Cage", "Pet Brush"],
    "Baby":           ["Bottle", "Pacifier", "Blanket", "Onesie", "Bib",
                       "Stroller", "Car Seat", "Monitor", "Diaper Bag", "Baby Toy"],
    "Tools":          ["Drill", "Screwdriver", "Wrench", "Hammer", "Pliers",
                       "Tape Measure", "Level", "Saw", "Clamp", "Sander"],
}


class ProductScraper:
    def __init__(self, target_count=15000, url=None):
        self.target_count = target_count
        self.url = url
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()
        self.products = []
        self.thread = None
        self.current = 0
        self.status_msg = "Ready"
        self.done = False
        self.error_msg = None
        self.on_finished = None

    def start(self):
        self._stop_event.clear()
        self._pause_event.set()
        self.done = False
        self.error_msg = None
        self.products = []
        self.current = 0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def pause(self):
        self._pause_event.clear()
        self.status_msg = "Paused"

    def resume(self):
        self._pause_event.set()
        self.status_msg = "Resuming..."

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()
        self.status_msg = "Stopped"

    def _run(self):
        try:
            self.status_msg = "Scraping from API..."
            api = self._scrape_api()
            self.products.extend(api)
            self.current = len(self.products)

            remaining = self.target_count - len(self.products)
            if remaining > 0 and not self._stop_event.is_set():
                self.status_msg = "Generating products..."
                self._generate(remaining)

            if not self._stop_event.is_set():
                self.status_msg = "Done!"
                self.done = True
                if self.on_finished:
                    self.on_finished(self.products)
        except Exception as e:
            self.error_msg = str(e)
            self.done = True

    def _scrape_api(self):
        products = []
        try:
            import urllib.request
            import json as _json
            base = self.url if self.url else "https://dummyjson.com/products"
            skip = 0
            limit = 100
            while not self._stop_event.is_set():
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break
                try:
                    req = urllib.request.Request(
                        f"{base}?limit={limit}&skip={skip}",
                        headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = _json.loads(resp.read().decode())
                    items = data.get("products", data if isinstance(data, list) else [])
                    if not items:
                        break
                    for item in items:
                        products.append({
                            "id": len(products) + 1,
                            "name": item.get("title", f"Product {len(products)+1}"),
                            "brand": item.get("brand", random.choice(BRANDS)),
                            "category": item.get("category", random.choice(CATEGORIES)),
                            "price": round(item.get("price", random.uniform(5, 500)), 2),
                            "rating": round(item.get("rating", random.uniform(1, 5)), 1),
                            "stock": item.get("stock", random.randint(0, 500)),
                            "discount": round(item.get("discountPercentage", random.uniform(0, 50)), 1),
                            "description": item.get("description", "No description"),
                            "sku": item.get("sku", f"SKU-{random.randint(10000,99999)}"),
                        })
                    self.current = len(products)
                    self.status_msg = f"Scraped {len(products)} from API..."
                    total = data.get("total", 0)
                    skip += limit
                    if skip >= total or len(items) < limit:
                        break
                except Exception:
                    break
        except Exception:
            pass
        return products

    def _generate(self, count):
        start_id = len(self.products) + 1
        for i in range(count):
            self._pause_event.wait()
            if self._stop_event.is_set():
                break
            cat = random.choice(CATEGORIES)
            ptype = random.choice(PRODUCT_TYPES.get(cat, ["Item"]))
            adj = random.choice(ADJECTIVES)
            brand = random.choice(BRANDS)
            self.products.append({
                "id": start_id + i,
                "name": f"{adj} {ptype} {random.randint(1, 999)}",
                "brand": brand,
                "category": cat,
                "price": round(random.uniform(1.99, 999.99), 2),
                "rating": round(random.uniform(1.0, 5.0), 1),
                "stock": random.randint(0, 1000),
                "discount": round(random.uniform(0, 60), 1),
                "description": f"{brand} {adj} {ptype} - High quality product",
                "sku": f"SKU-{random.randint(10000, 99999)}",
            })
            if (i + 1) % 200 == 0 or i == count - 1:
                self.current = len(self.products)
                self.status_msg = f"Generated {self.current} products..."


def save_products(products, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(products, f)


def load_products(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
