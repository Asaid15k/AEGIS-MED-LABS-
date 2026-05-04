import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="aegis_mdlbs_db",   # ✅ YOUR DB NAME
    user="postgres",
    password="1234"       # ✅ SAME AS db_config.py
)

cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
tables = cur.fetchall()

print("Tables:")
for t in tables:
    print(t)

conn.close()