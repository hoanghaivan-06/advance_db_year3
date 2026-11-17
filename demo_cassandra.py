from datetime import date, datetime
from cassandra import InvalidRequest
from cassandra.cluster import Cluster

cluster = Cluster(["127.0.0.1"])
session = cluster.connect()

session.execute("""
    CREATE KEYSPACE IF NOT EXISTS shop
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
""")
session.set_keyspace("shop")

session.execute("""
    CREATE TABLE IF NOT EXISTS readings_by_sensor (
        sensor_id   text,
        ts          timestamp,
        temperature double,
        humidity    double,
        PRIMARY KEY ((sensor_id), ts)
    ) WITH CLUSTERING ORDER BY (ts DESC)
""")

insert = session.prepare(
    "INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity) "
    "VALUES (?, ?, ?, ?)"
)
session.execute(insert, ("hn-01", datetime(2026, 10, 22, 8, 0), 27.5, 71.0))
session.execute(insert, ("hn-01", datetime(2026, 10, 22, 8, 5), 27.8, 70.0))
session.execute(insert, ("hn-02", datetime(2026, 10, 22, 8, 0), 25.1, 80.0))
session.execute(insert, ("hn-01", datetime(2026, 10, 22, 8, 10), 28.0, 69.0))

rows = session.execute(
    "SELECT ts, temperature FROM readings_by_sensor WHERE sensor_id = %s LIMIT 5",
    ("hn-01",),
)
for row in rows:
    print(row.ts, row.temperature)

# Exercises
# 1. Create a table that answers "latest 10 orders of a customer" and a second one for "orders per day".
session.execute("""
    CREATE TABLE IF NOT EXISTS orders_by_customer (
        customer_id text,
        ts          timestamp,
        order_id    int,
        total       double,
        PRIMARY KEY ((customer_id), ts, order_id)
    ) WITH CLUSTERING ORDER BY (ts DESC)
""")

session.execute("""
    CREATE TABLE IF NOT EXISTS orders_by_day (
        day         date,
        ts          timestamp,
        order_id    int,
        customer_id text,
        total       double,
        PRIMARY KEY ((day), ts, order_id)
    ) WITH CLUSTERING ORDER BY (ts DESC)
""")

session.execute(
    "INSERT INTO orders_by_customer (customer_id, ts, order_id, total) VALUES (%s, %s, %s, %s)",
    ("linh", datetime(2026, 10, 22, 9, 0), 1001, 43.0),
)
session.execute(
    "INSERT INTO orders_by_day (day, ts, order_id, customer_id, total) VALUES (%s, %s, %s, %s, %s)",
    (date(2026, 10, 22), datetime(2026, 10, 22, 9, 0), 1001, "linh", 43.0),
)

print("Latest orders of linh:", list(session.execute(
    "SELECT * FROM orders_by_customer WHERE customer_id = 'linh' LIMIT 10"
)))
print("Orders on 2026-10-22:", list(session.execute(
    "SELECT * FROM orders_by_day WHERE day = '2026-10-22'"
)))

# 2. Insert readings for three sensors and try a query that omits the partition key. Read the error.
session.execute(insert, ("hn-03", datetime(2026, 10, 22, 8, 0), 29.0, 65.0))
try:
    session.execute("SELECT * FROM readings_by_sensor WHERE temperature > 27")
except InvalidRequest as e:
    print("Expected error when omitting partition key:", e)

# 3. Change the schema to a monthly partition bucket and explain why.
# Why: Partitioning by ((sensor_id, month), ts) keeps each partition bounded in size (<100 MB)
# instead of growing indefinitely over the lifetime of a sensor.
session.execute("""
    CREATE TABLE IF NOT EXISTS readings_by_sensor_monthly (
        sensor_id   text,
        month       text,
        ts          timestamp,
        temperature double,
        humidity    double,
        PRIMARY KEY ((sensor_id, month), ts)
    ) WITH CLUSTERING ORDER BY (ts DESC)
""")
session.execute(
    "INSERT INTO readings_by_sensor_monthly (sensor_id, month, ts, temperature, humidity) "
    "VALUES (%s, %s, %s, %s, %s)",
    ("hn-01", "2026-10", datetime(2026, 10, 22, 8, 10), 28.0, 69.0),
)
print("Monthly bucket query:", list(session.execute(
    "SELECT ts, temperature FROM readings_by_sensor_monthly WHERE sensor_id = 'hn-01' AND month = '2026-10' LIMIT 5"
)))

cluster.shutdown()
