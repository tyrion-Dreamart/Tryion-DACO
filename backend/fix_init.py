# Leer el archivo
with open('app/models/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar invoice_quotes a los imports si no está
if 'invoice_quotes' not in content:
    # Agregar a la lista de imports
    content = content.replace(
        'InvoicePayment,',
        'InvoicePayment,\\n    invoice_quotes,'
    )
    
    # Agregar a __all__
    content = content.replace(
        '"InvoicePayment",',
        '"InvoicePayment",\\n    "invoice_quotes",'
    )
    
    with open('app/models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('invoice_quotes agregado a __init__.py')
else:
    print('invoice_quotes ya existe en __init__.py')
