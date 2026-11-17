import json
import time
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def slow_query(product_id: int) -> dict:
    time.sleep(1)                                   # pretend this hits a database
    return {"id": product_id, "title": "Python Basics", "price": 12.5}

def get_product(product_id: int) -> dict:
    key = f"product:{product_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)                   # hit: fast
    product = slow_query(product_id)                # miss: slow
    r.set(key, json.dumps(product), ex=300)         # keep for 5 minutes
    return product

r.flushdb()
start = time.perf_counter(); get_product(7); print(f"first : {time.perf_counter() - start:.3f}s")
start = time.perf_counter(); get_product(7); print(f"second: {time.perf_counter() - start:.3f}s")

def allow(user: str, limit: int = 5) -> bool:
    key = f"rate:{user}:{int(time.time() // 60)}"   # one counter per minute
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)
    return count <= limit

# Exercises
# 1. Build a leaderboard with a sorted set and print the top 3 players with their ranks.
r.zadd("board", {"linh": 1200, "nam": 950, "mai": 1430, "an": 1100, "binh": 1350})
for rank, (player, score) in enumerate(r.zrevrange("board", 0, 2, withscores=True), start=1):
    print(f"#{rank}: {player} ({score})")

# 2. Store user profiles as hashes and find users in a city using a set per city.
users = [
    ("42", {"name": "Linh", "city": "Hanoi", "age": "21"}),
    ("43", {"name": "Nam", "city": "Da Nang", "age": "22"}),
    ("44", {"name": "Mai", "city": "Hanoi", "age": "20"}),
]
for uid, profile in users:
    r.hset(f"user:{uid}", mapping=profile)
    r.sadd(f"city:{profile['city'].lower()}", uid)

for uid in r.smembers("city:hanoi"):
    print(uid, r.hgetall(f"user:{uid}"))

# 3. Measure the speed-up of the cache-aside example for 100 repeated requests.
r.delete("product:7")
t0 = time.perf_counter()
for _ in range(100):
    get_product(7)
cached_total = time.perf_counter() - t0
uncached_total = 100 * 1.0                          # 100 calls * 1s slow_query each
print(f"100 requests with cache: {cached_total:.3f}s vs without cache: ~{uncached_total:.1f}s (speed-up: {uncached_total / cached_total:.1f}x)")
