import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
orders = client.shop.orders

orders.insert_one({"_id": 1004, "customer": {"name": "Hung", "city": "Hue"},
                   "status": "paid", "items": []})

for doc in orders.find({"status": "paid"}, {"customer.name": 1, "status": 1}):
    print(doc)

pipeline = [
    {"$unwind": "$items"},
    {"$group": {"_id": "$items.sku", "units": {"$sum": "$items.qty"}}},
]
df = pd.DataFrame(orders.aggregate(pipeline))      # straight into pandas
print(df)

# Exercises
# 1. Insert five orders with different shapes, then find all orders containing a given sku.
orders.insert_many([
    {"customer": {"name": "An", "city": "Hanoi"}, "status": "paid",
     "items": [{"sku": "BK-01", "qty": 2, "price": 12.5}], "coupon": "SALE10"},
    {"customer": {"name": "Binh", "city": "Hue"}, "status": "shipped",
     "items": [{"sku": "BK-02", "qty": 1, "price": 30.0}], "gift": True},
    {"customer": {"name": "Chi", "city": "Da Nang"}, "status": "paid",
     "items": [{"sku": "BK-01", "qty": 3, "price": 12.5}], "tags": ["urgent"]},
    {"customer": {"name": "Dung", "city": "Hanoi"}, "status": "paid",
     "items": [{"sku": "BK-07", "qty": 1, "price": 18.0}], "shipping_fee": 2.5},
    {"customer": {"name": "Ha", "city": "Hue"}, "status": "shipped",
     "items": [{"sku": "BK-01", "qty": 1, "price": 12.5}], "note": "call before delivery"},
])

for doc in orders.find({"items.sku": "BK-01"}):
    print(doc)

# 2. Write an aggregation that returns revenue per city.
city_pipeline = [
    {"$unwind": "$items"},
    {"$group": {
        "_id": "$customer.city",
        "revenue": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}},
    }},
    {"$sort": {"revenue": -1}},
]
print(pd.DataFrame(orders.aggregate(city_pipeline)))

# 3. Create an index and compare explain() before and after on 10,000 generated documents.
orders.drop_indexes()
cities = ["Hanoi", "Da Nang", "Hue", "HCMC"]
statuses = ["paid", "shipped", "pending"]
orders.insert_many([
    {
        "customer": {"name": f"User{i}", "city": cities[i % 4]},
        "status": statuses[i % 3],
        "items": [{"sku": "BK-01", "qty": 1, "price": 12.5}],
    }
    for i in range(10000)
])

before = orders.find({"customer.city": "Hanoi", "status": "paid"}).explain()["executionStats"]
print("Before index:", before["totalDocsExamined"], "docs examined,", before["executionTimeMillis"], "ms")

orders.create_index([("customer.city", 1), ("status", 1)])

after = orders.find({"customer.city": "Hanoi", "status": "paid"}).explain()["executionStats"]
print("After index:", after["totalDocsExamined"], "docs examined,", after["executionTimeMillis"], "ms")
