-- Create the application database user (non-superuser) for RLS enforcement.
-- This script runs automatically on first `docker compose up` via
-- PostgreSQL's /docker-entrypoint-initdb.d/ mechanism.

-- The database itself (crm_db) is created by POSTGRES_DB env var.
-- We just need to create the app user and grant privileges.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'crm_user') THEN
        CREATE ROLE crm_user WITH LOGIN PASSWORD 'crm_password';
    END IF;
END
$$;

-- Grant privileges on the database
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;

-- Allow crm_user to create schemas and objects in the public schema
\connect crm_db;
GRANT ALL ON SCHEMA public TO crm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO crm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO crm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO crm_user;
