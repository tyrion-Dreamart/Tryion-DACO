import psycopg2

conn = psycopg2.connect('postgresql://daco:daco_secret@localhost:5432/daco')
cur = conn.cursor()

# Ver que columnas tiene invoices actualmente
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'invoices' 
    ORDER BY ordinal_position
""")
print('=== COLUMNAS DE invoices ===')
for row in cur.fetchall():
    print(f'  {row[0]}')

# Ver los datos actuales
print()
print('=== DATOS DE invoices ===')
cur.execute("""
    SELECT id, invoice_number, issue_date, status, total, legal_entity_id 
    FROM invoices 
    LIMIT 10
""")
for row in cur.fetchall():
    print(f'ID: {row[0]} | Numero: {row[1]} | Fecha: {row[2]} | Estado: {row[3]} | Total: {row[4]} | LegalEntity: {row[5]}')

# Ver si hay columnas viejas que quizas aun existan
print()
print('=== VERIFICANDO COLUMNAS ANTIGUAS ===')
for col in ['folio', 'client_id', 'quote_id', 'balance', 'paid_amount', 'iva_amount', 'pdf_url', 'exchange_rate']:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'invoices' AND column_name = %s
    """, (col,))
    result = cur.fetchone()
    if result:
        print(f'  {col}: EXISTS')
    else:
        print(f'  {col}: NOT FOUND')

cur.close()
conn.close()