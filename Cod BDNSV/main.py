import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pymongo import MongoClient
import redis

app = FastAPI(title="Gift Shop DENEX - Redis Caching Demo")

mongo_client = MongoClient("mongodb://admin:parola_secreta@localhost:27017/")
db = mongo_client["ecommerce_db"]
collection = db["products"]

# Redis salveaza datele in binar, parametrul decode_responses=True ajuta la afisarea sub forma de string-uri
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@app.get("/")
def read_root():
    return {"status": "online"}

# ---------------------------------------------------------
# STRATEGIA 1: CACHE-ASIDE
# Verifica daca datele sunt in Redis
# HIT: Daca gaseste datele in Redis, le returneaza
# MISS: Daca nu sunt acolo, le cauta in MongoDB, le salveaza in Redis, apoi le returneaza
# ---------------------------------------------------------
@app.get("/products/{product_id}")
def get_product(product_id: int, simulate_delay: bool = False):
    start_time = time.time()
    redis_key = f"product:{product_id}"
    
    product_data = r.hgetall(redis_key)
    # HIT
    if product_data:
        if 'price' in product_data: product_data['price'] = float(product_data['price'])
        if 'product_id' in product_data: product_data['product_id'] = int(product_data['product_id'])
        if 'stock' in product_data: product_data['stock'] = int(product_data['stock'])
        if 'views' in product_data: product_data['views'] = int(product_data['views'])
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        return {
            "strategy": "Cache-Aside (HIT)",
            "source": "Redis Cache",
            "execution_time_ms": f"{duration_ms:.2f} ms", 
            "data": product_data
        }

    # MISS
    if simulate_delay:
        time.sleep(0.05)
    
    product_db = collection.find_one({"product_id": product_id}, {"_id": 0})
    
    if not product_db:
        raise HTTPException(status_code=404, detail="Produsul nu a fost gasit")

    # Scriem produsul in Redis
    redis_mapping = {k: str(v) for k, v in product_db.items()}
    r.hset(redis_key, mapping=redis_mapping)
    r.expire(redis_key, 1800) #TTL = 30 minute

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    return {
        "strategy": "Cache-Aside (MISS)",
        "source": "MongoDB",
        "execution_time_ms": f"{duration_ms:.2f} ms",
        "data": product_db
    }

# ---------------------------------------------------------
# STRATEGIA 2: WRITE-THROUGH
# Datele sunt scrise in MongoDB si in Redis
# ---------------------------------------------------------
@app.put("/products/{product_id}/price")
def update_price(product_id: int, new_price: float, simulate_delay: bool = False):
    start_time = time.time()
    redis_key = f"product:{product_id}"

    if simulate_delay:
        time.sleep(0.05)
    
    # Update MongoDB
    result = collection.update_one(
        {"product_id": product_id},
        {"$set": {"price": new_price}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Produsul nu exista")

    # Update Redis
    cache_msg = "Produsul nu se afla in Redis"
    if r.exists(redis_key):
        r.hset(redis_key, "price", str(new_price))
        cache_msg = "Pretul a fost updatat."

    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    return {
        "strategy": "Write-Through",
        "status": "Succes",
        "execution_time_ms": f"{duration_ms:.2f} ms",
        "details": f"Pretul a fost actualizat in MongoDB si Redis. Cache status: {cache_msg}"
    }

# ---------------------------------------------------------
# STRATEGIA 3: WRITE-BEHIND
# ---------------------------------------------------------
def sync_views_to_db(product_id: int, views: int):
    collection.update_one({"product_id": product_id}, {"$set": {"views": views}})
    print(f"   [Background] Vizualizari salvate pentru produsul {product_id} in MongoDB.")

@app.post("/products/{product_id}/view")
def view_product(product_id: int, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    # Update Redis
    r.zincrby("leaderboard", 1, f"product:{product_id}")
    new_views = r.incr(f"product:{product_id}:views")
    
    user_history_key = "user:1:history"
    r.lpush(user_history_key, product_id)
    r.ltrim(user_history_key, 0, 4)

    # Trimite task spre DB
    background_tasks.add_task(sync_views_to_db, product_id, new_views)
    
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000

    return {
        "strategy": "Write-Behind",
        "execution_time_ms": f"{duration_ms:.2f} ms",
        "current_views": new_views,
        "message": "Vizualizare inregistrata in Redis. MongoDB se va actualiza in fundal."
    }

@app.get("/leaderboard")
def get_leaderboard():
    start = time.time()
    top = r.zrevrange("leaderboard", 0, 9, withscores=True)
    duration = (time.time() - start) * 1000
    
    data = [{"product": m, "views": int(s)} for m, s in top]
    return {"source": "Redis Sorted Set", "time_ms": f"{duration:.2f}", "top_products": data}

@app.get("/my-history")
def get_history():
    start_time = time.time()
    user_history_key = "user:1:history"
    
    history_ids = r.lrange(user_history_key, 0, -1)
    
    products_details = []
    
    for pid in history_ids:
        redis_key = f"product:{pid}"
        
        name = r.hget(redis_key, "name")
        price = r.hget(redis_key, "price")
        
        if not name:
             products_details.append({"product_id": pid, "status": "Expired from Cache (TTL)"})
        else:
             products_details.append({
                 "product_id": pid, 
                 "name": name, 
                 "price": float(price) if price else 0.0
             })

    duration_ms = (time.time() - start_time) * 1000
    
    return {
        "source": "Redis List (LRANGE)",
        "execution_time_ms": f"{duration_ms:.2f} ms",
        "recent_products": products_details
    }