from sqlalchemy import Table, Column, String, ForeignKey
from app.db.base import Base

# Tabla de asociacion many-to-many entre invoices y quotes
invoice_quotes = Table(
    'invoice_quotes',
    Base.metadata,
    Column('invoice_id', String(36), ForeignKey('invoices.id', ondelete='CASCADE'), primary_key=True),
    Column('quote_id', String(36), ForeignKey('quotes.id', ondelete='CASCADE'), primary_key=True),
)
