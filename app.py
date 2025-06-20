from flask import Flask, jsonify, send_file
import pymysql
import redis
import json

app = Flask(__name__)

# Redis config
redis_client = redis.Redis(
    host='test-3ozrrc.serverless.use2.cache.amazonaws.com',  // Replace Your Redis host end-point
    port=6379,
    ssl=True,  # Enable TLS for ElastiCache Redis
    decode_responses=True,
    socket_timeout=5
)

# RDS config
RDS_HOST = 'database-1.chi6cwg4csb9.us-east-2.rds.amazonaws.com' // Replace Your DB Endpoint
RDS_USER = 'admin' // Replace your user-name
RDS_PASSWORD = 'Devops123' // Replace your password
RDS_DB_NAME = 'test' // Replace your DB Name
TABLE_NAME = 'users' // Replace your Table Name

CACHE_KEY = 'cached_table_data'

def fetch_data_from_rds():
    try:
        connection = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB_NAME
        )
        print("🔗 Connected to RDS")

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 10;")
            rows = cursor.fetchall()
            return rows

    except Exception as e:
        print("❌ RDS Error:", e)
        return None

    finally:
        if 'connection' in locals():
            connection.close()

def get_from_cache_or_rds():
    cached_data = redis_client.get(CACHE_KEY)
    if cached_data:
        print("✅ Fetched from Redis cache")
        data = json.loads(cached_data)
        return jsonify(data)
    else:
        print("⚙️ No cache found. Fetching from RDS...")
        data = fetch_data_from_rds()
        if data:
            redis_client.set(CACHE_KEY, json.dumps(data), ex=90)  # Cache expires in 90 seconds
            print("📦 Cached in Redis")
            return jsonify(data)
        else:
            return jsonify([]), 500

def refresh_from_rds():
    data = fetch_data_from_rds()
    if data:
        redis_client.set(CACHE_KEY, json.dumps(data), ex=90)
        print("🔄 Cache refreshed from RDS")
        return jsonify(data)
    else:
        return jsonify([]), 500

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/get-data')
def get_data():
    return get_from_cache_or_rds()

@app.route('/refresh')
def refresh():
    return refresh_from_rds()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
