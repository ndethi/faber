-- Initial schema for faber-cms
-- Run with: wrangler d1 execute faber-cms-content --file=./migrations/0001_initial.sql

-- Collections registry
CREATE TABLE IF NOT EXISTS collections (
  name TEXT PRIMARY KEY,
  schema TEXT NOT NULL,
  ui_config TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Content entries (polymorphic across collections)
-- Each collection gets its own table: content_{collection_name}
-- This is a template - actual tables created dynamically per collection
CREATE TABLE IF NOT EXISTS content_template (
  id TEXT PRIMARY KEY,
  collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  version INTEGER NOT NULL DEFAULT 1,
  data TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  slug TEXT
);

-- Indexes for content tables (created per collection)
-- CREATE INDEX idx_content_{name}_collection ON content_{name}(collection_id);
-- CREATE INDEX idx_content_{name}_status ON content_{name}(status);
-- CREATE INDEX idx_content_{name}_slug ON content_{name}(slug);
-- CREATE INDEX idx_content_{name}_published_at ON content_{name}(published_at);
-- CREATE UNIQUE INDEX uq_content_{name}_collection_slug ON content_{name}(collection_id, slug);

-- Media assets (R2-backed)
CREATE TABLE IF NOT EXISTS media (
  id TEXT PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size INTEGER NOT NULL,
  metadata TEXT NOT NULL,
  uploaded_by TEXT NOT NULL,
  uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_media_key ON media(key);
CREATE INDEX IF NOT EXISTS idx_media_uploaded_by ON media(uploaded_by);

-- Users (synced from CF Access)
CREATE TABLE IF NOT EXISTS users (
  email TEXT PRIMARY KEY,
  role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'editor', 'viewer')),
  name TEXT,
  avatar_url TEXT,
  last_login TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Site settings
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT NOT NULL,
  updated_by TEXT NOT NULL
);

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  events TEXT NOT NULL,
  secret TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT NOT NULL
);

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  scopes TEXT NOT NULL,
  prefix TEXT NOT NULL,
  hashed_key TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT NOT NULL,
  expires_at TEXT,
  last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_email TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  before_json TEXT,
  after_json TEXT,
  ip TEXT,
  user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_email ON audit_log(user_email);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Trigger to update updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_collections_timestamp
AFTER UPDATE ON collections
BEGIN
  UPDATE collections SET updated_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
END;

CREATE TRIGGER IF NOT EXISTS update_media_timestamp
AFTER UPDATE ON media
BEGIN
  UPDATE media SET uploaded_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
BEGIN
  UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE email = NEW.email;
END;

CREATE TRIGGER IF NOT EXISTS update_settings_timestamp
AFTER UPDATE ON settings
BEGIN
  UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;

CREATE TRIGGER IF NOT EXISTS update_webhooks_timestamp
AFTER UPDATE ON webhooks
BEGIN
  UPDATE webhooks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_api_keys_timestamp
AFTER UPDATE ON api_keys
BEGIN
  UPDATE api_keys SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;