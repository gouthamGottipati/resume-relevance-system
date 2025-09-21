-- Initialize production database with optimizations

-- Create database if not exists (this file runs after DB is created, so mainly for configuration)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create indexes for better performance
-- These will be created after tables are created via SQLAlchemy
-- The indexes are defined here as a reference for production optimization

-- Example performance optimizations:
-- CREATE INDEX CONCURRENTLY idx_resumes_skills_gin ON resumes USING gin (skills);
-- CREATE INDEX CONCURRENTLY idx_resumes_candidate_name ON resumes (candidate_name);
-- CREATE INDEX CONCURRENTLY idx_evaluations_score ON resume_evaluations (overall_score DESC);
-- CREATE INDEX CONCURRENTLY idx_evaluations_created_at ON resume_evaluations (created_at DESC);

-- Grant permissions (adjust as needed for production)
GRANT ALL PRIVILEGES ON DATABASE resume_ai TO postgres;