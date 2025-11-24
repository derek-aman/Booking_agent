from pymongo import MongoClient

MONGO_URI = "your_connection_string_here"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)

try:
    print(client.list_database_names())
    print("✅ Connected successfully")
except Exception as e:
    print("❌ Connection failed:", e)

