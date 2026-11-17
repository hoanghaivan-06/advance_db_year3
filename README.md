# Thực hành NoSQL Databases (MongoDB, Redis, Cassandra, Neo4j)

Kho lưu trữ bao gồm mã nguồn thực hành và lời giải bài tập cho các hệ cơ sở dữ liệu NoSQL:
- **01 - Document Store (MongoDB):** `demo_mongodb.js`, `demo_mongodb.py`
- **02 - Key-Value Store (Redis):** `demo_redis.py`, `ticketrush.py` (Lab TicketRush)
- **03 - Column-Family Database (Cassandra):** `demo_cassandra.cql`, `demo_cassandra.py`, `sensorring/` (Lab SensorRing 3-node cluster)
- **04 - Graph Database (Neo4j):** `demo_neo4j.cypher`, `demo_neo4j.py`, `campus.py` (Lab CampusGraph), `import/people.csv`

---

## 1. Cài đặt môi trường ảo Python (`venv`)

Mở Terminal / PowerShell tại thư mục gốc của dự án và chạy các lệnh sau:

### Trên Windows (PowerShell):
```powershell
# 1. Tạo môi trường ảo
python -m venv venv

# 2. Kích hoạt môi trường ảo
.\venv\Scripts\Activate.ps1

# 3. Cài đặt toàn bộ thư viện cần thiết
pip install -r requirements.txt
```
*(Nếu không kích hoạt `Activate.ps1`, bạn có thể gọi trực tiếp `.\venv\Scripts\pip install -r requirements.txt` và chạy file bằng `.\venv\Scripts\python <ten_file>.py`).*

### Trên macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Khởi chạy các hệ CSDL bằng Docker Compose

Yêu cầu cài đặt sẵn **Docker Desktop**. Khởi chạy từng dịch vụ tương ứng trước khi chạy code:

```powershell
# Bài 1: MongoDB (cổng 27017)
docker compose up -d mongo
python demo_mongodb.py

# Bài 2: Redis (cổng 6379)
docker compose up -d redis
python demo_redis.py
python ticketrush.py

# Bài 3: Cassandra (cổng 9042 - đợi khoảng 60 giây để Cassandra khởi động xong)
docker compose up -d cassandra
python demo_cassandra.py

# Bài 4: Neo4j (cổng 7474 / 7687 - tài khoản: neo4j / learnneo4j)
docker compose up -d neo4j
python demo_neo4j.py
python campus.py check
```
