# Leer el archivo
with open('app/models/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya existe invoice_quotes
if 'invoice_quotes' not in content:
    # Agregar import de Table y Column si no están
    if 'from sqlalchemy import (' in content and 'Table' not in content.split('from sqlalchemy import (')[1].split(')')[0]:
        content = content.replace(
            'from sqlalchemy import (',
            'from sqlalchemy import (\\n    Table,'
        )
    
    # Agregar la tabla invoice_quotes después de los imports
    insert_after = 'from app.db.base import Base\\n'
    invoice_quotes_table = '''\\n# Tabla de asociacion many-to-many entre invoices y quotes\\ninvoice_quotes = Table(\\n    'invoice_quotes',\\n    Base.metadata,\\n    Column('invoice_id', String(36), ForeignKey('invoices.id', ondelete='CASCADE'), primary_key=True),\\n    Column('quote_id', String(36), ForeignKey('quotes.id', ondelete='CASCADE'), primary_key=True),\\n)\\n'''
    
    content = content.replace(insert_after, insert_after + invoice_quotes_table)
    
    # Guardar
    with open('app/models/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('Tabla invoice_quotes agregada a models.py')
else:
    print('La tabla invoice_quotes ya existe en models.py')
