CREATE KEYSPACE IF NOT EXISTS shop
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE shop;

CREATE TABLE IF NOT EXISTS readings_by_sensor (
    sensor_id   text,
    ts          timestamp,
    temperature double,
    humidity    double,
    PRIMARY KEY ((sensor_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-01', '2026-10-22 08:00:00', 27.5, 71);
INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-01', '2026-10-22 08:05:00', 27.8, 70);
INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-02', '2026-10-22 08:00:00', 25.1, 80);

SELECT * FROM readings_by_sensor WHERE sensor_id = 'hn-01' LIMIT 10;

SELECT * FROM readings_by_sensor
WHERE sensor_id = 'hn-01' AND ts >= '2026-10-22 08:02:00';

-- Exercises
-- 1. Create a table that answers "latest 10 orders of a customer" and a second one for "orders per day".
CREATE TABLE IF NOT EXISTS orders_by_customer (
    customer_id text,
    ts          timestamp,
    order_id    int,
    total       double,
    PRIMARY KEY ((customer_id), ts, order_id)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS orders_by_day (
    day         date,
    ts          timestamp,
    order_id    int,
    customer_id text,
    total       double,
    PRIMARY KEY ((day), ts, order_id)
) WITH CLUSTERING ORDER BY (ts DESC);

INSERT INTO orders_by_customer (customer_id, ts, order_id, total) VALUES ('linh', '2026-10-22 09:00:00', 1001, 43.0);
INSERT INTO orders_by_day (day, ts, order_id, customer_id, total) VALUES ('2026-10-22', '2026-10-22 09:00:00', 1001, 'linh', 43.0);

SELECT * FROM orders_by_customer WHERE customer_id = 'linh' LIMIT 10;
SELECT * FROM orders_by_day WHERE day = '2026-10-22';

-- 2. Insert readings for three sensors and try a query that omits the partition key. Read the error.
INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-03', '2026-10-22 08:00:00', 29.0, 65);

SELECT * FROM readings_by_sensor WHERE temperature > 27;

-- 3. Change the schema to a monthly partition bucket and explain why.
-- Reason: Adding `month` to the partition key ((sensor_id, month), ts) bounds each partition's size
-- (under 100 MB) instead of letting one sensor's partition grow forever across years.
CREATE TABLE IF NOT EXISTS readings_by_sensor_monthly (
    sensor_id   text,
    month       text,
    ts          timestamp,
    temperature double,
    humidity    double,
    PRIMARY KEY ((sensor_id, month), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

INSERT INTO readings_by_sensor_monthly (sensor_id, month, ts, temperature, humidity)
VALUES ('hn-01', '2026-10', '2026-10-22 08:00:00', 27.5, 71);

SELECT * FROM readings_by_sensor_monthly WHERE sensor_id = 'hn-01' AND month = '2026-10' LIMIT 10;
