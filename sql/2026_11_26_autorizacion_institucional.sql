-- Rizoma 2.3.0 (26/11/2026): habilitación institucional, sesiones revocables y trazabilidad de credenciales.
-- Para instalaciones existentes: aplicar ANTES de reiniciar con el código nuevo (el modelo ya lee estas columnas).
-- En una instalación nueva no cambia nada. Las tablas auth_limits y security_audit se crean al iniciar.
ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_verified BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS sessions_valid_after DOUBLE PRECISION NOT NULL DEFAULT 0;
ALTER TABLE credentials ADD COLUMN IF NOT EXISTS verified_by UUID REFERENCES users(id);
ALTER TABLE credentials ADD COLUMN IF NOT EXISTS verification_note TEXT DEFAULT '';
