import type { D1Database, KVNamespace, R2Bucket } from "@cloudflare/workers-types";

export interface Env {
  DB: D1Database;
  SESSIONS: KVNamespace;
  MEDIA: R2Bucket;
  CF_ACCESS_TEAM_DOMAIN: string;
  CF_ACCESS_AUD: string;
  CF_ACCESS_PUBLIC_KEY: string;
  PREVIEW_SECRET: string;
  PREVIEW_BASE: string;
  ENVIRONMENT: "development" | "staging" | "production";
  GITHUB_TOKEN?: string;
  GITHUB_OWNER?: string;
  GITHUB_REPO?: string;
}

export interface CfAccessPayload {
  email: string;
  sub: string;
  aud: string | string[];
  groups?: string[];
  exp: number;
  iat: number;
}

export interface User {
  email: string;
  role: "admin" | "editor" | "viewer";
  name?: string;
  avatar_url?: string;
  last_login?: string;
}

export interface ContentEntry {
  id: string;
  collection: string;
  slug: string;
  data: string; // JSON string
  status: "draft" | "published" | "archived";
  version: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  created_by: string;
  updated_by: string;
}

export interface Collection {
  name: string;
  schema: string; // Zod schema as JSON
  ui_config: string; // Field widgets, validation, preview config
}

export interface MediaAsset {
  id: string;
  key: string; // R2 object key
  url: string; // Public/signed URL
  mime_type: string;
  size: number;
  metadata: string; // JSON
  uploaded_by: string;
  uploaded_at: string;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  before_json: string | null;
  after_json: string | null;
  ip: string | null;
  user_agent: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
}

export interface PreviewPayload {
  id: string;
  version: number;
  exp: number;
}