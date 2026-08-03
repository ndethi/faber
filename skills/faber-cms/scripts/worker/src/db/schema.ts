import { sqliteTable, text, integer, blob, index, uniqueIndex } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const collections = sqliteTable("collections", {
  name: text("name").primaryKey(),
  schema: text("schema").notNull(), // Zod schema as JSON
  uiConfig: text("ui_config").notNull(), // Field widgets, validation, preview config
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
});

export const content = sqliteTable("content", {
  id: text("id").primaryKey(), // UUID
  collection: text("collection").notNull().references(() => collections.name, { onDelete: "cascade" }),
  slug: text("slug").notNull(),
  data: text("data").notNull(), // JSON string
  status: text("status", { enum: ["draft", "published", "archived"] }).notNull().default("draft"),
  version: integer("version").notNull().default(1),
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
  publishedAt: text("published_at"),
  createdBy: text("created_by").notNull(),
  updatedBy: text("updated_by").notNull(),
}, (table) => ({
  collectionIdx: index("idx_content_collection").on(table.collection),
  statusIdx: index("idx_content_status").on(table.status),
  slugIdx: index("idx_content_slug").on(table.slug),
  publishedAtIdx: index("idx_content_published_at").on(table.publishedAt),
  collectionSlugUnique: uniqueIndex("uq_content_collection_slug").on(table.collection, table.slug),
}));

export const media = sqliteTable("media", {
  id: text("id").primaryKey(), // UUID
  key: text("key").notNull().unique(), // R2 object key
  url: text("url").notNull(), // Public/signed URL
  mimeType: text("mime_type").notNull(),
  size: integer("size").notNull(),
  metadata: text("metadata").notNull(), // JSON string
  uploadedBy: text("uploaded_by").notNull(),
  uploadedAt: text("uploaded_at").default(sql`CURRENT_TIMESTAMP`),
}, (table) => ({
  keyIdx: index("idx_media_key").on(table.key),
  uploadedByIdx: index("idx_media_uploaded_by").on(table.uploadedBy),
}));

export const users = sqliteTable("users", {
  email: text("email").primaryKey(),
  role: text("role", { enum: ["admin", "editor", "viewer"] }).notNull().default("viewer"),
  name: text("name"),
  avatarUrl: text("avatar_url"),
  lastLogin: text("last_login"),
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
});

export const settings = sqliteTable("settings", {
  key: text("key").primaryKey(),
  value: text("value").notNull(), // JSON string
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
  createdBy: text("created_by").notNull(),
  updatedBy: text("updated_by").notNull(),
});

export const webhooks = sqliteTable("webhooks", {
  id: text("id").primaryKey(),
  url: text("url").notNull(),
  events: text("events").notNull(), // JSON array
  secret: text("secret"),
  active: integer("active", { mode: "boolean" }).notNull().default(true),
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
  createdBy: text("created_by").notNull(),
});

export const apiKeys = sqliteTable("api_keys", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  scopes: text("scopes").notNull(), // JSON array
  prefix: text("prefix").notNull(),
  hashedKey: text("hashed_key").notNull(),
  createdAt: text("created_at").default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").default(sql`CURRENT_TIMESTAMP`),
  createdBy: text("created_by").notNull(),
  expiresAt: text("expires_at"),
  lastUsedAt: text("last_used_at"),
}, (table) => ({
  prefixIdx: index("idx_api_keys_prefix").on(table.prefix),
}));

export const auditLog = sqliteTable("audit_log", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  timestamp: text("timestamp").notNull().default(sql`CURRENT_TIMESTAMP`),
  userEmail: text("user_email").notNull(),
  action: text("action").notNull(),
  resourceType: text("resource_type").notNull(),
  resourceId: text("resource_id").notNull(),
  beforeJson: text("before_json"),
  afterJson: text("after_json"),
  ip: text("ip"),
  userAgent: text("user_agent"),
}, (table) => ({
  timestampIdx: index("idx_audit_log_timestamp").on(table.timestamp),
  userEmailIdx: index("idx_audit_log_user_email").on(table.userEmail),
  resourceIdx: index("idx_audit_log_resource").on(table.resourceType, table.resourceId),
}));

export type Collection = typeof collections.$inferSelect;
export type NewCollection = typeof collections.$inferInsert;
export type Content = typeof content.$inferSelect;
export type NewContent = typeof content.$inferInsert;
export type Media = typeof media.$inferSelect;
export type NewMedia = typeof media.$inferInsert;
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Settings = typeof settings.$inferSelect;
export type NewSettings = typeof settings.$inferInsert;
export type Webhook = typeof webhooks.$inferSelect;
export type NewWebhook = typeof webhooks.$inferInsert;
export type ApiKey = typeof apiKeys.$inferSelect;
export type NewApiKey = typeof apiKeys.$inferInsert;
export type AuditLog = typeof auditLog.$inferSelect;
export type NewAuditLog = typeof auditLog.$inferInsert;