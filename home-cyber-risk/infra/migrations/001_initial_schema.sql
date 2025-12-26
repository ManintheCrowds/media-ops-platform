-- Initial database schema for SQLite
-- This is automatically created by SQLAlchemy, but provided for reference

CREATE TABLE IF NOT EXISTS breaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(50) NOT NULL,
    breach_name VARCHAR(255) NOT NULL,
    breach_date DATETIME,
    data_classes TEXT,  -- JSON stored as TEXT in SQLite
    pwn_count INTEGER,
    description VARCHAR(1000),
    is_verified BOOLEAN DEFAULT 1 NOT NULL,
    domain VARCHAR(255),
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    notified BOOLEAN DEFAULT 0 NOT NULL,
    raw_data TEXT  -- JSON stored as TEXT in SQLite
);

CREATE INDEX IF NOT EXISTS idx_breaches_identifier ON breaches(identifier);
CREATE INDEX IF NOT EXISTS idx_breaches_breach_name ON breaches(breach_name);
CREATE INDEX IF NOT EXISTS idx_breaches_identifier_breach ON breaches(identifier, breach_name);
CREATE INDEX IF NOT EXISTS idx_breaches_first_seen ON breaches(first_seen);
CREATE INDEX IF NOT EXISTS idx_breaches_notified ON breaches(notified);

CREATE TABLE IF NOT EXISTS check_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(50) NOT NULL,
    check_time DATETIME NOT NULL,
    breaches_found INTEGER DEFAULT 0 NOT NULL,
    new_breaches INTEGER DEFAULT 0 NOT NULL,
    updated_breaches INTEGER DEFAULT 0 NOT NULL,
    success BOOLEAN DEFAULT 1 NOT NULL,
    error_message VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_check_history_identifier ON check_history(identifier);
CREATE INDEX IF NOT EXISTS idx_check_history_check_time ON check_history(check_time);

