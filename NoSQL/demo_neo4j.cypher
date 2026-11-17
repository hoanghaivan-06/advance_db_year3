// Reset database before running
MATCH (n) DETACH DELETE n;

// 1. Create sample data
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
       (mai)-[:BOUGHT {year: 2026}]->(viz);

// 2. Reading data: MATCH, WHERE, RETURN
MATCH (p:Person {city: "Hanoi"}) RETURN p.name;

MATCH (p:Person)
WHERE p.city = "Hanoi" AND p.age >= 21
RETURN p.name, p.age
ORDER BY p.age DESC;

MATCH (:Person {name: "Linh"})-[b:BOUGHT]->(book:Book)
RETURN book.title, b.year;

MATCH (:Person {name: "Mai"})-[:FRIEND]-(f:Person)
RETURN f.name;

// OPTIONAL MATCH
MATCH (p:Person)
OPTIONAL MATCH (p)-[:BOUGHT]->(b:Book)
RETURN p.name, count(b) AS books;

// 3. Aggregation, WITH and lists
MATCH (p:Person)-[:BOUGHT]->(b:Book)
RETURN p.name AS person,
       count(b) AS books,
       sum(b.price) AS spent,
       collect(b.title) AS titles
ORDER BY spent DESC;

MATCH (p:Person)-[r:BOUGHT]->(:Book)
WHERE r.year = 2026
WITH p, count(*) AS n
WHERE n > 1
RETURN p.name, n;

MATCH (b:Book)<-[:BOUGHT]-(p:Person)
WITH b, count(p) AS buyers
ORDER BY buyers DESC, b.title
LIMIT 1
MATCH (b)<-[:BOUGHT]-(p:Person)
RETURN b.title, collect(p.name) AS buyers;

// UNWIND and list expressions
UNWIND [
  {name: "Tuan", city: "Hanoi"},
  {name: "Vy",   city: "Can Tho"}
] AS row
MERGE (p:Person {name: row.name})
SET p.city = row.city;

MATCH (p:Person)
RETURN p.name,
       [(p)-[:BOUGHT]->(b) | b.title] AS books,
       [x IN range(1, 5) WHERE x % 2 = 1 | x * x] AS odd_squares;

// Subquery expressions: EXISTS and COUNT
MATCH (p:Person)
WHERE COUNT { (p)-[:FRIEND]-() } >= 2
RETURN p.name;

MATCH (b:Book)
WHERE NOT EXISTS { (b)<-[:BOUGHT]-(:Person {city: "Hanoi"}) }
RETURN b.title;

// 4. Paths & Recommendations
MATCH (:Person {name: "Linh"})-[:FRIEND*2]->(fof:Person)
RETURN fof.name;

MATCH path = (:Person {name: "Linh"})-[:FRIEND*1..3]->(other:Person)
RETURN other.name, length(path) AS hops, [n IN nodes(path) | n.name] AS route
ORDER BY hops;

MATCH (a:Person {name: "Linh"}), (b:Person {name: "Hung"}),
      p = shortestPath((a)-[:FRIEND*..10]-(b))
RETURN [n IN nodes(p) | n.name] AS route, length(p) AS hops;

MATCH (me:Person {name: "Linh"})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS recommendation, count(*) AS friends_who_bought
ORDER BY friends_who_bought DESC;

MATCH (:Book {title: "Python Basics"})<-[:BOUGHT]-(p:Person)-[:BOUGHT]->(other:Book)
WHERE other.title <> "Python Basics"
RETURN other.title, count(DISTINCT p) AS also_bought
ORDER BY also_bought DESC;

// 5. Writing data & MERGE
MATCH (p:Person {name: "Tuan"}) DETACH DELETE p;
MATCH (p:Person {name: "Vy"}) DETACH DELETE p;

MERGE (p:Person {name: "Linh"})
ON CREATE SET p.createdAt = datetime()
ON MATCH  SET p.lastSeen  = datetime();

// 6. LOAD CSV
LOAD CSV WITH HEADERS FROM "file:///people.csv" AS row
MERGE (p:Person {name: row.name})
SET p.city = row.city, p.age = toInteger(row.age);

// 7. Indexes and constraints
CREATE CONSTRAINT person_name IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE INDEX person_city IF NOT EXISTS FOR (p:Person) ON (p.city);

CREATE FULLTEXT INDEX book_titles IF NOT EXISTS FOR (b:Book) ON EACH [b.title];

SHOW INDEXES;
SHOW CONSTRAINTS;

// 8. Graph algorithms in plain Cypher
MATCH (p:Person)
RETURN p.name, COUNT { (p)-[:FRIEND]-() } AS degree
ORDER BY degree DESC;

MATCH (a:Person {name: "Linh"})-[:BOUGHT]->(b:Book)
WITH a, collect(b) AS mine
MATCH (other:Person)-[:BOUGHT]->(b:Book) WHERE other <> a
WITH mine, other, collect(b) AS theirs
RETURN other.name,
       toFloat(size([x IN mine WHERE x IN theirs])) /
       size(mine + [x IN theirs WHERE NOT x IN mine]) AS jaccard
ORDER BY jaccard DESC;

// ============================================================================
// Exercises
// ============================================================================

// 1. Add five more people and friendships to the shop graph, then find friends-of-friends of Linh who live in Hanoi.
UNWIND [
  {name: "An",   city: "Hanoi", age: 21},
  {name: "Binh", city: "Hanoi", age: 22},
  {name: "Chi",  city: "Hue",   age: 20},
  {name: "Dung", city: "Hanoi", age: 23},
  {name: "Ha",   city: "Da Nang", age: 21}
] AS row
MERGE (p:Person {name: row.name})
SET p.city = row.city, p.age = row.age;

MATCH (linh:Person {name: "Linh"}), (nam:Person {name: "Nam"}), (mai:Person {name: "Mai"}),
      (an:Person {name: "An"}), (binh:Person {name: "Binh"}), (chi:Person {name: "Chi"}),
      (dung:Person {name: "Dung"}), (ha:Person {name: "Ha"})
MERGE (linh)-[:FRIEND]->(chi)
MERGE (chi)-[:FRIEND]->(an)
MERGE (nam)-[:FRIEND]->(binh)
MERGE (mai)-[:FRIEND]->(dung)
MERGE (an)-[:FRIEND]->(ha);

MATCH (linh:Person {name: "Linh"})-[:FRIEND*2]-(fof:Person {city: "Hanoi"})
WHERE fof <> linh AND NOT (linh)-[:FRIEND]-(fof)
RETURN DISTINCT fof.name AS fof_in_hanoi;

// 2. Write a query that recommends books to Mai, and one that lists, for each person, the total they spent.
MATCH (me:Person {name: "Mai"})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS recommendation, count(DISTINCT friend) AS friends_who_bought
ORDER BY friends_who_bought DESC;

MATCH (p:Person)
OPTIONAL MATCH (p)-[:BOUGHT]->(b:Book)
RETURN p.name AS person, coalesce(sum(b.price), 0) AS total_spent
ORDER BY total_spent DESC;

// 3. Model a metro network with :Station nodes and :NEXT {minutes: 3} relationships,
// then find the route with the fewest stops between two stations.
CREATE (s1:Station {name: "Cat Linh"})-[:NEXT {minutes: 3}]->
       (s2:Station {name: "La Thanh"})-[:NEXT {minutes: 3}]->
       (s3:Station {name: "Thai Ha"})-[:NEXT {minutes: 3}]->
       (s4:Station {name: "Lang"})-[:NEXT {minutes: 4}]->
       (s5:Station {name: "Thuong Dinh"});

MATCH (a:Station {name: "Cat Linh"}), (b:Station {name: "Thuong Dinh"}),
      p = shortestPath((a)-[:NEXT*..15]-(b))
RETURN [s IN nodes(p) | s.name] AS route, length(p) AS stops;

// 4. Model an employment history (person, company, role, start and end date) twice:
// once with relationship properties and once with an intermediate node.
// Model A: Relationship properties
MERGE (p:Person {name: "Linh"})
MERGE (c:Company {name: "FPT"})
MERGE (p)-[:WORKED_AT {role: "Data Engineer", startDate: date("2025-01-01"), endDate: date("2026-01-01")}]->(c);

// Model B: Intermediate :Employment node (allows linking projects, skills, location to a specific job stint)
MERGE (p2:Person {name: "Linh"})
MERGE (c2:Company {name: "FPT"})
CREATE (e:Employment {role: "Data Engineer", startDate: date("2025-01-01"), endDate: date("2026-01-01")})
MERGE (p2)-[:HELD]->(e)
MERGE (e)-[:AT_COMPANY]->(c2);

// 5. Profile MATCH (p:Person {name: "Linh"}) RETURN p before and after creating the uniqueness constraint.
DROP CONSTRAINT person_name IF EXISTS;
PROFILE MATCH (p:Person {name: "Linh"}) RETURN p;

CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
PROFILE MATCH (p:Person {name: "Linh"}) RETURN p;
