-- Initialize PDFChat database
-- This file is executed when the PostgreSQL container starts

-- Create UUID extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE pdfchat TO postgres;