import psycopg2

conn = psycopg2.connect('postgresql://daco:daco_secret@localhost:5432/daco')
cur = conn.cursor()

# Buscar tablas relacionadas con invoice
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%invoice%'
""")
print('=== TABLAS RELACIONADAS CON INVOICE ===')
for row in cur.fetchall():
    print(f'  {row[0]}')

# Buscar tablas de log o historial
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%log%' OR table_name LIKE '%history%' OR table_name LIKE '%audit%')
""")
print()
print('=== TABLAS DE LOG/HISTORIAL ===')
for row in cur.fetchall():
    print(f'  {row[0]}')

# Ver si hay alguna tabla que tenga folios o numeros
cur.execute("""
    SELECT table_name, column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND (column_name LIKE '%folio%' OR column_name LIKE '%number%' OR column_name LIKE '%numero%')
""")
print()
print('=== COLUMNAS CON FOLIO/NUMERO ===')
for row in cur.fetchall():
    print(f'  Tabla: {row[0]} | Columna: {row[1]}')

cur.close()
conn.close()
