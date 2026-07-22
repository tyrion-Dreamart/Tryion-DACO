import psycopg2

conn = psycopg2.connect('postgresql://daco:daco_secret@localhost:5432/daco')
cur = conn.cursor()

print('=== TABLA: invoice_payments ===')
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'invoice_payments' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable={row[2]})")

print()
print('=== TABLA: invoices ===')
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'invoices' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable={row[2]})")

print()
print('=== ENUMS ===')
cur.execute("""
    SELECT typname FROM pg_type 
    WHERE typtype = 'e'
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

cur.close()
conn.close()