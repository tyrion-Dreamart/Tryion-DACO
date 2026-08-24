-- DACO Database Initialization
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search

-- Schemas (for future module separation)
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS crm;

-- Default search_path
ALTER DATABASE daco SET search_path TO public, core, billing, crm;

-- Useful indexes will be created by Alembic migrations
