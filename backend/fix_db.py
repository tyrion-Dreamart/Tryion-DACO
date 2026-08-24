import psycopg2

with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('DATABASE_URL='):
            db_url = line.strip().split('=', 1)[1].strip()
            if db_url[0] in '"'"'" and db_url[-1] == db_url[0]:
                db_url = db_url[1:-1]
            break

print('DB_URL:', db_url[:60])

conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("ALTER TABLE corporates ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(255)")
conn.commit()
cur.close()
conn.close()
print('Hecho!')