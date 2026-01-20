import time
from faker import Faker
from pymongo import MongoClient
import random

MONGO_URI = "mongodb://admin:parola_secreta@localhost:27017/"
DB_NAME = "ecommerce_db"
COLLECTION_NAME = "products"

fake = Faker()

CATEGORY_CONFIG = {
    "Gadgets & Tech": {
        "nouns": ["Headphones", "Powerbank", "Smartwatch", "Speaker", "VR Headset", "Drone", "Keyboard", "Tablet", "Mouse", "Monitor", "Webcam", "Microphone", "Router"],
        "adjectives": ["Wireless", "Smart", "High-Performance", "Compact", "Noise-Cancelling", "Ergonomic", "Fast-Charging", "Waterproof", "Bluetooth", "4K", "Digital"],
        "desc_templates": [
            "Experience the future with this {adj} {noun}. Features a {num}h battery life and seamless connectivity.",
            "The new {noun} offers {adj} performance for professionals. Includes a 2-year warranty.",
            "Upgrade your setup with our {adj} {noun}. Designed in {city} for maximum efficiency.",
            "Top-rated {noun} with {adj} technology. Perfect for daily use and travel."
        ]
    },
    "Books & Stationery": {
        "nouns": ["Journal", "Fountain Pen", "Planner", "Sketchbook", "Novel", "Organizer", "Bookmark", "Reading Light", "Notebook", "Pencil Case", "Calendar"],
        "adjectives": ["Leather-Bound", "Classic", "Refillable", "Vintage", "Minimalist", "Hardcover", "Pocket-Sized", "Handmade", "Premium", "Matte"],
        "desc_templates": [
            "Write your thoughts in this {adj} {noun}. Made from {material} with high-quality paper.",
            "A perfect gift for writers: the {adj} {noun}. Comes in a beautiful gift box.",
            "Stay organized with our {adj} {noun}. Bestseller in {city} bookshops.",
            "This {noun} features a {adj} design, perfect for school or office use."
        ]
    },
    "Home & Decor": {
        "nouns": ["Candle", "Vase", "Blanket", "Lamp", "Pillow", "Diffuser", "Clock", "Pot", "Mirror", "Rug", "Curtains", "Statue", "Tray"],
        "adjectives": ["Cozy", "Modern", "Rustic", "Decorative", "Soft", "Ambient", "Handwoven", "Ceramic", "Glass", "Minimalist", "Velvet"],
        "desc_templates": [
            "Add a touch of style with this {adj} {noun}. Perfect for your living room.",
            "Create a {adj} atmosphere with our best-selling {noun}. Made of 100% {material}.",
            "This {noun} is handcrafted and features a unique {adj} finish.",
            "Transform your home with this {adj} {noun}. Dimensions: {num}x{num} cm."
        ]
    },
    "Gourmet & Sweets": {
        "nouns": ["Chocolate Box", "Coffee Beans", "Tea Set", "Truffle Oil", "Macarons", "Spices", "Honey", "Cheese Board", "Cookies", "Jam"],
        "adjectives": ["Delicious", "Organic", "Gourmet", "Artisan", "Sweet", "Spicy", "Dark", "Creamy", "Fresh", "Authentic"],
        "desc_templates": [
            "Indulge in the rich taste of our {adj} {noun}. Sourced directly from {country}.",
            "A treat for your senses: {adj} {noun}. Contains natural ingredients and no preservatives.",
            "Perfect for sharing: this {adj} {noun} is a customer favorite.",
            "Experience the flavor of {adj} {noun}. Best enjoyed with a cup of coffee."
        ]
    },
    "Wellness & Spa": {
        "nouns": ["Essential Oils", "Bath Bomb", "Robe", "Face Mask", "Yoga Mat", "Sleep Mask", "Manicure Kit", "Salt Lamp", "Body Scrub", "Towel"],
        "adjectives": ["Relaxing", "Soothing", "Natural", "Luxury", "Calming", "Aromatic", "Soft", "Rejuvenating", "Detox", "Organic"],
        "desc_templates": [
            "Relax after a long day with our {adj} {noun}. Infused with natural scents.",
            "Treat yourself to a spa day at home with this {adj} {noun}.",
            "This {noun} provides a {adj} experience. Recommended by wellness experts.",
            "Feel the difference with our {adj} {noun}. Made with skin-friendly materials."
        ]
    },
    "Toys & Board Games": {
        "nouns": ["Board Game", "Teddy Bear", "RC Car", "Puzzle", "Action Figure", "Building Blocks", "Robot", "Doll", "Chess Set", "Dice Set"],
        "adjectives": ["Fun", "Educational", "Interactive", "Colorful", "Plush", "Strategic", "Family-Friendly", "Durable", "Collectible"],
        "desc_templates": [
            "Hours of fun guaranteed with this {adj} {noun}. Suitable for ages {num}+.",
            "The perfect gift for kids: a {adj} {noun} that sparks creativity.",
            "Challenge your friends with this {adj} {noun}. Includes detailed instructions.",
            "A high-quality {noun} with {adj} features. Limited edition release."
        ]
    },
    "Jewelry & Watches": {
        "nouns": ["Necklace", "Bracelet", "Watch", "Earrings", "Ring", "Cufflinks", "Brooch", "Pendant", "Choker"],
        "adjectives": ["Silver", "Gold-Plated", "Elegant", "Diamond", "Luxury", "Vintage", "Sparkling", "Minimalist", "Sapphire"],
        "desc_templates": [
            "Shine bright with this {adj} {noun}. Crafted with precision.",
            "A timeless piece: the {adj} {noun}. Perfect for anniversaries.",
            "This {noun} features a {adj} design. Comes with a certificate of authenticity.",
            "Elevate your style with our {adj} {noun}. Waterproof and durable."
        ]
    },
    "DIY & Hobbies": {
        "nouns": ["Knitting Kit", "Painting Set", "Model Ship", "Gardening Tools", "Origami Paper", "Chisel Set", "Pottery Wheel", "Sketch Pad"],
        "adjectives": ["Creative", "Beginner-Friendly", "Pro", "Complete", "Artistic", "Detailed", "Handy", "Durable"],
        "desc_templates": [
            "Unleash your creativity with this {adj} {noun}. Includes all necessary tools.",
            "Start your new hobby with our {adj} {noun}. Step-by-step guide included.",
            "This {noun} is perfect for {adj} projects. High-quality materials.",
            "Build your own masterpiece with the {adj} {noun}."
        ]
    }
}

MATERIALS = ["Leather", "Silk", "Wood", "Metal", "Glass", "Cotton", "Wool", "Bamboo", "Plastic", "Steel", "Velvet"]
CATEGORIES_LIST = list(CATEGORY_CONFIG.keys())

def generate_product(i, generated_names):
    category = random.choice(CATEGORIES_LIST)
    config = CATEGORY_CONFIG[category]
    
    noun = random.choice(config["nouns"])
    adjective = random.choice(config["adjectives"])
    
    name_style = random.randint(1, 3)
    product_name = ""
    
    if name_style == 1:
        series_name = fake.word().capitalize()
        product_name = f"{adjective} {noun} '{series_name}' Series"
    elif name_style == 2:
        prefix = random.choice(["Premium", "The Ultimate", "Classic", "New", "Limited"])
        product_name = f"{prefix} {adjective} {noun}"
    else:
        year = fake.year()
        product_name = f"{adjective} {noun} Model {year}"

    if product_name in generated_names:
        product_name = f"{product_name} (v{i})"
    generated_names.add(product_name)

    template = random.choice(config["desc_templates"])
    
    description = template.format(
        adj=adjective.lower(),
        noun=noun.lower(),
        material=random.choice(MATERIALS).lower(),
        city=fake.city(),
        country=fake.country(),
        num=random.randint(2, 100)
    )

    return {
        "product_id": i + 1,
        "name": product_name,
        "description": description,
        "price": round(random.uniform(15.0, 3500.0), 2),
        "category": category,
        "stock": random.randint(0, 500),
        "views": 0,
        "image_url": fake.image_url(),
        "created_at": fake.date_time_this_year().isoformat()
    }

def seed_database():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        if collection.count_documents({}) > 0:
            print("Stergem datele vechi...")
            collection.delete_many({})

        print("Generam 10.000 de produse...")
        start_time = time.time()
        
        products_data = []
        generated_names = set()
        
        for i in range(10000):
            prod = generate_product(i, generated_names)
            products_data.append(prod)
            
            if (i+1) % 2000 == 0:
                print(f"   ... s-au generat {i+1} produse")

        print("Inseram datele in MongoDB...")
        collection.insert_many(products_data)
        
        duration = time.time() - start_time
        print(f"SUCCES! Produsele au fost inserate in {duration:.2f} secunde.")

    except Exception as e:
        print(f"Eroare: {e}")

if __name__ == "__main__":
    seed_database()