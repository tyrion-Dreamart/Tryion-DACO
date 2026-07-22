"""add_payment_cross_currency_fields

Revision ID: 3ebd933536e3
Revises: caa9ec852cdd
Create Date: 2026-07-22 13:53:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3ebd933536e3'
down_revision = 'caa9ec852cdd'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Crear enum payment_method ─────────────────────────────────────────
    payment_method = postgresql.ENUM('CASH', 'TRANSFER', 'CHECK', 'CARD', 'OTHER', name='payment_method')
    payment_method.create(op.get_bind())

    # ─── Tabla invoices: agregar columnas nuevas ───────────────────────────
    op.add_column('invoices', sa.Column('legal_entity_id', sa.String(length=36), nullable=True))
    op.create_index('ix_invoices_legal_entity_id', 'invoices', ['legal_entity_id'], unique=False)
    op.create_foreign_key('fk_invoices_legal_entity', 'invoices', 'legal_entities', ['legal_entity_id'], ['id'], ondelete='CASCADE')

    op.add_column('invoices', sa.Column('contact_id', sa.String(length=36), nullable=True))
    op.create_index('ix_invoices_contact_id', 'invoices', ['contact_id'], unique=False)
    op.create_foreign_key('fk_invoices_contact', 'invoices', 'contacts', ['contact_id'], ['id'], ondelete='SET NULL')

    op.add_column('invoices', sa.Column('invoice_number', sa.String(length=50), nullable=True))
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'], unique=False)

    op.add_column('invoices', sa.Column('tax_amount', sa.Numeric(precision=15, scale=2), nullable=True))

    # ─── Tabla invoice_payments: agregar columnas nuevas ───────────────────
    # PASO 1: Agregar payment_method como NULLABLE primero
    op.add_column('invoice_payments', sa.Column('payment_method', sa.Enum('CASH', 'TRANSFER', 'CHECK', 'CARD', 'OTHER', name='payment_method'), nullable=True))
    
    # PASO 2: Llenar filas existentes con valor por defecto
    op.execute("UPDATE invoice_payments SET payment_method = 'TRANSFER' WHERE payment_method IS NULL")
    
    # PASO 3: Hacerla NOT NULL
    op.alter_column('invoice_payments', 'payment_method', nullable=False)

    # Resto de columnas (con server_default para filas existentes)
    op.add_column('invoice_payments', sa.Column('invoice_currency', sa.String(length=3), nullable=False, server_default='MXN'))
    op.add_column('invoice_payments', sa.Column('payment_currency', sa.String(length=3), nullable=False, server_default='MXN'))
    op.add_column('invoice_payments', sa.Column('exchange_rate', sa.Numeric(precision=15, scale=6), nullable=True))
    op.add_column('invoice_payments', sa.Column('amount_in_invoice_currency', sa.Numeric(precision=15, scale=2), nullable=True))
    op.add_column('invoice_payments', sa.Column('recorded_by_id', sa.String(length=36), nullable=True))

    # Foreign key a users
    op.create_foreign_key('fk_invoice_payments_user', 'invoice_payments', 'users', ['recorded_by_id'], ['id'], ondelete='SET NULL')

    # Modificar columnas existentes
    op.alter_column('invoice_payments', 'amount',
               existing_type=sa.NUMERIC(precision=14, scale=2),
               type_=sa.Numeric(precision=15, scale=2),
               existing_nullable=False)
    op.alter_column('invoice_payments', 'reference',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=100),
               existing_nullable=True)


def downgrade():
    # ─── Revertir invoice_payments ─────────────────────────────────────────
    op.drop_constraint('fk_invoice_payments_user', 'invoice_payments', type_='foreignkey')

    op.alter_column('invoice_payments', 'reference',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    op.alter_column('invoice_payments', 'amount',
               existing_type=sa.Numeric(precision=15, scale=2),
               type_=sa.NUMERIC(precision=14, scale=2),
               existing_nullable=False)

    op.drop_column('invoice_payments', 'recorded_by_id')
    op.drop_column('invoice_payments', 'amount_in_invoice_currency')
    op.drop_column('invoice_payments', 'exchange_rate')
    op.drop_column('invoice_payments', 'payment_currency')
    op.drop_column('invoice_payments', 'invoice_currency')
    op.drop_column('invoice_payments', 'payment_method')

    # ─── Revertir invoices ─────────────────────────────────────────────────
    op.drop_constraint('fk_invoices_contact', 'invoices', type_='foreignkey')
    op.drop_constraint('fk_invoices_legal_entity', 'invoices', type_='foreignkey')
    op.drop_index('ix_invoices_contact_id', table_name='invoices')
    op.drop_index('ix_invoices_invoice_number', table_name='invoices')
    op.drop_index('ix_invoices_legal_entity_id', table_name='invoices')
    op.drop_column('invoices', 'contact_id')
    op.drop_column('invoices', 'invoice_number')
    op.drop_column('invoices', 'tax_amount')
    op.drop_column('invoices', 'legal_entity_id')

    # ─── Eliminar enum ─────────────────────────────────────────────────────
    payment_method = postgresql.ENUM('CASH', 'TRANSFER', 'CHECK', 'CARD', 'OTHER', name='payment_method')
    payment_method.drop(op.get_bind())