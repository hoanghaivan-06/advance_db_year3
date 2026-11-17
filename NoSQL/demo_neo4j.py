import neo4j
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "learnneo4j")

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

# Setup initial shop graph from the lesson
driver.execute_query("MATCH (n) DETACH DELETE n")
driver.execute_query("""
CREATE (linh:Person {name: "Linh", city: "Hanoi", age: 21}),
       (nam:Person  {name: "Nam",  city: "Da Nang", age: 22}),
       (mai:Person  {name: "Mai",  city: "Hanoi", age: 20}),
       (hung:Person {name: "Hung", city: "Hue", age: 23}),
       (py:Book  {title: "Python Basics", price: 120000}),
       (sql:Book {title: "SQL in Practice", price: 150000}),
       (viz:Book {title: "Data Viz", price: 135000}),
       (linh)-[:FRIEND {since: 2023}]->(nam),
       (nam)-[:FRIEND {since: 2024}]->(mai),
       (mai)-[:FRIEND {since: 2025}]->(hung),
       (linh)-[:BOUGHT {year: 2026}]->(py),
       (linh)-[:BOUGHT {year: 2026}]->(sql),
       (nam)-[:BOUGHT {year: 2025}]->(sql),
       (nam)-[:BOUGHT {year: 2026}]->(viz),
       (mai)-[:BOUGHT {year: 2026}]->(py),
       (mai)-[:BOUGHT {year: 2026}]->(viz)
""")

QUERY = """
MATCH (me:Person {name: $name})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS title, count(*) AS score
ORDER BY score DESC
"""

records, summary, keys = driver.execute_query(QUERY, name="Linh")
for record in records:
    print(record["title"], record["score"])
print(f"{summary.result_available_after} ms")

df = driver.execute_query(
    "MATCH (p:Person) RETURN p.name AS name, p.city AS city, p.age AS age",
    result_transformer_=neo4j.Result.to_df,
)
print(df.groupby("city")["age"].mean())

def transfer_friend(tx, person, old_friend, new_friend):
    tx.run("""MATCH (:Person {name: $p})-[f:FRIEND]-(:Person {name: $o}) DELETE f""",
           p=person, o=old_friend)
    tx.run("""MATCH (a:Person {name: $p}), (b:Person {name: $n})
              MERGE (a)-[:FRIEND]->(b)""", p=person, n=new_friend)

with driver.session(database="neo4j") as session:
    session.execute_write(transfer_friend, "Linh", "Nam", "Mai")
    # Restore original friendship for the exercises below
    session.execute_write(transfer_friend, "Linh", "Mai", "Nam")

# Exercises
# 1. Add five more people and friendships to the shop graph, then find friends-of-friends of Linh who live in Hanoi.
driver.execute_query("""
    UNWIND $rows AS row
    MERGE (p:Person {name: row.name})
    SET p.city = row.city, p.age = row.age
""", rows=[
    {"name": "An",   "city": "Hanoi",   "age": 21},
    {"name": "Binh", "city": "Hanoi",   "age": 22},
    {"name": "Chi",  "city": "Hue",     "age": 20},
    {"name": "Dung", "city": "Hanoi",   "age": 23},
    {"name": "Ha",   "city": "Da Nang", "age": 21},
])
driver.execute_query("""
    MATCH (linh:Person {name: "Linh"}), (nam:Person {name: "Nam"}), (mai:Person {name: "Mai"}),
          (an:Person {name: "An"}), (binh:Person {name: "Binh"}), (chi:Person {name: "Chi"}),
          (dung:Person {name: "Dung"}), (ha:Person {name: "Ha"})
    MERGE (linh)-[:FRIEND]->(chi)
    MERGE (chi)-[:FRIEND]->(an)
    MERGE (nam)-[:FRIEND]->(binh)
    MERGE (mai)-[:FRIEND]->(dung)
    MERGE (an)-[:FRIEND]->(ha)
""")
fof_records, _, _ = driver.execute_query("""
    MATCH (linh:Person {name: "Linh"})-[:FRIEND*2]-(fof:Person {city: "Hanoi"})
    WHERE fof <> linh AND NOT (linh)-[:FRIEND]-(fof)
    RETURN DISTINCT fof.name AS name ORDER BY name
""")
print("Ex 1 - Friends-of-friends of Linh in Hanoi:", [r["name"] for r in fof_records])

# 2. Write a query that recommends books to Mai, and one that lists, for each person, the total they spent.
mai_recs, _, _ = driver.execute_query(QUERY, name="Mai")
print("Ex 2a - Book recommendations for Mai:", [(r["title"], r["score"]) for r in mai_recs])

spent_df = driver.execute_query("""
    MATCH (p:Person)
    OPTIONAL MATCH (p)-[:BOUGHT]->(b:Book)
    RETURN p.name AS person, coalesce(sum(b.price), 0) AS total_spent
    ORDER BY total_spent DESC, person ASC
""", result_transformer_=neo4j.Result.to_df)
print("Ex 2b - Total spent per person:\n", spent_df.to_string(index=False))

# 3. Model a metro network with :Station nodes and :NEXT {minutes: 3} relationships,
# then find the route with the fewest stops between two stations.
driver.execute_query("""
    CREATE (:Station {name: "Cat Linh"})-[:NEXT {minutes: 3}]->
           (:Station {name: "La Thanh"})-[:NEXT {minutes: 3}]->
           (:Station {name: "Thai Ha"})-[:NEXT {minutes: 3}]->
           (:Station {name: "Lang"})-[:NEXT {minutes: 4}]->
           (:Station {name: "Thuong Dinh"})
""")
metro_res, _, _ = driver.execute_query("""
    MATCH (a:Station {name: "Cat Linh"}), (b:Station {name: "Thuong Dinh"}),
          p = shortestPath((a)-[:NEXT*..15]-(b))
    RETURN [s IN nodes(p) | s.name] AS route, length(p) AS stops
""")
print("Ex 3 - Metro route:", metro_res[0]["route"], "| stops:", metro_res[0]["stops"])

# 4. Model an employment history (person, company, role, start and end date) twice:
# once with relationship properties and once with an intermediate node.
driver.execute_query("""
    MERGE (p:Person {name: "Linh"})
    MERGE (c:Company {name: "FPT"})
    MERGE (p)-[:WORKED_AT {role: "Data Engineer", start: "2025-01", end: "2026-01"}]->(c)
    CREATE (e:Employment {role: "Data Engineer", start: "2025-01", end: "2026-01"})
    MERGE (p)-[:HELD]->(e)-[:AT_COMPANY]->(c)
""")
print("Ex 4 - Employment modeled both via [:WORKED_AT] relationship properties and via (:Employment) node.")

# 5. Profile MATCH (p:Person {name: "Linh"}) RETURN p before and after creating the uniqueness constraint.
def first_op(plan):
    while plan.get("children"):
        plan = plan["children"][0]
    return plan.get("operatorType"), plan.get("dbHits")

driver.execute_query("DROP CONSTRAINT person_name IF EXISTS")
_, summary_before, _ = driver.execute_query("PROFILE MATCH (p:Person {name: 'Linh'}) RETURN p")

driver.execute_query("CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")
_, summary_after, _ = driver.execute_query("PROFILE MATCH (p:Person {name: 'Linh'}) RETURN p")

print("Ex 5 - Before constraint:", first_op(summary_before.profile))
print("Ex 5 - After constraint :", first_op(summary_after.profile))

driver.close()
