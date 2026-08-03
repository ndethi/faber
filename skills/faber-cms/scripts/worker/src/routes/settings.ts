import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { sql } from "drizzle-orm";
import type { Env } from "../types";
import { getDb, schema } from "../db";

const settingsRoutes = new Hono<Env>();

const siteConfigSchema = z.object({
  siteName: z.string().optional(),
  siteDescription: z.string().optional(),
  siteUrl: z.string().url().optional(),
  socialLinks: z.record(z.string().url()).optional(),
  analytics: z.object({
    provider: z.enum(["plausible", "ga4", "none"]).optional(),
    id: z.string().optional(),
    domain: z.string().optional(),
  }).optional(),
});

settingsRoutes.get("/site", async (c) => {
  const db = getDb(c.env);
  const config = await db.select().from(schema.settings).where(sql`${schema.settings.key} = 'site'`).get();
  return c.json(config?.value ? JSON.parse(config.value) : {});
});

settingsRoutes.put("/site", zValidator("json", siteConfigSchema), async (c) => {
  const user = c.get("user");
  const config = c.req.valid("json");
  const db = getDb(c.env);
  const now = new Date().toISOString();

  const existing = await db.select().from(schema.settings).where(sql`${schema.settings.key} = 'site'`).get();

  if (existing) {
    await db.update(schema.settings)
      .set({ value: JSON.stringify(config), updatedAt: now, updatedBy: user.email })
      .where(sql`${schema.settings.key} = 'site'`);
  } else {
    await db.insert(schema.settings).values({
      key: "site",
      value: JSON.stringify(config),
      createdAt: now,
      updatedAt: now,
      createdBy: user.email,
      updatedBy: user.email,
    });
  }

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "update",
    resourceType: "settings",
    resourceId: "site",
    beforeJson: existing?.value || null,
    afterJson: JSON.stringify(config),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json(config);
});

const webhookSchema = z.object({
  url: z.string().url(),
  events: z.array(z.enum(["publish", "update", "delete", "media_upload"])).min(1),
  secret: z.string().min(16).max(64).optional(),
  active: z.boolean().default(true),
});

settingsRoutes.get("/webhooks", async (c) => {
  const db = getDb(c.env);
  const webhooks = await db.select().from(schema.webhooks).all();
  return c.json({ webhooks });
});

settingsRoutes.post("/webhooks", zValidator("json", webhookSchema), async (c) => {
  const user = c.get("user");
  const webhook = c.req.valid("json");
  const db = getDb(c.env);
  const now = new Date().toISOString();
  const id = crypto.randomUUID();

  await db.insert(schema.webhooks).values({
    id,
    ...webhook,
    createdAt: now,
    updatedAt: now,
    createdBy: user.email,
  });

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "create",
    resourceType: "webhook",
    resourceId: id,
    afterJson: JSON.stringify(webhook),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ id, ...webhook }, 201);
});

settingsRoutes.put("/webhooks/:id", zValidator("json", webhookSchema.partial()), async (c) => {
  const user = c.get("user");
  const id = c.req.param("id");
  const updates = c.req.valid("json");
  const db = getDb(c.env);
  const now = new Date().toISOString();

  const existing = await db.select().from(schema.webhooks).where(sql`${schema.webhooks.id} = ${id}`).get();
  if (!existing) return c.json({ error: "Not found" }, 404);

  await db.update(schema.webhooks).set({ ...updates, updatedAt: now }).where(sql`${schema.webhooks.id} = ${id}`);

  const updated = await db.select().from(schema.webhooks).where(sql`${schema.webhooks.id} = ${id}`).get();

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "update",
    resourceType: "webhook",
    resourceId: id,
    beforeJson: JSON.stringify(existing),
    afterJson: JSON.stringify(updated),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json(updated);
});

settingsRoutes.delete("/webhooks/:id", async (c) => {
  const user = c.get("user");
  const id = c.req.param("id");
  const db = getDb(c.env);

  const existing = await db.select().from(schema.webhooks).where(sql`${schema.webhooks.id} = ${id}`).get();
  if (!existing) return c.json({ error: "Not found" }, 404);

  await db.delete(schema.webhooks).where(sql`${schema.webhooks.id} = ${id}`);

  await db.insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "delete",
    resourceType: "webhook",
    resourceId: id,
    beforeJson: JSON.stringify(existing),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ success: true });
});

const apiKeySchema = z.object({
  name: z.string().min(1).max(64),
  scopes: z.array(z.enum(["read", "write", "admin"])).min(1),
  expiresAt: z.string().datetime().optional(),
});

settingsRoutes.get("/api-keys", async (c) => {
  const db = getDb(c.env);
  const keys = await db.select({
    id: schema.apiKeys.id,
    name: schema.apiKeys.name,
    scopes: schema.apiKeys.scopes,
    prefix: schema.apiKeys.prefix,
    createdAt: schema.apiKeys.createdAt,
    expiresAt: schema.apiKeys.expiresAt,
    lastUsedAt: schema.apiKeys.lastUsedAt,
  }).from(schema.apiKeys).all();
  return c.json({ apiKeys: keys });
});

settingsRoutes.post("/api-keys", zValidator("json", apiKeySchema), async (c) => {
  const user = c.get("user");
  const { name, scopes, expiresAt } = c.req.valid("json");
  const db = getDb(c.env);
  const now = new Date().toISOString();
  const id = crypto.randomUUID();
  const prefix = `fcm_${crypto.randomBytes(4).toString("hex")}`;
  const key = `${prefix}_${crypto.randomBytes(24).toString("base64url")}`;
  const hashed = await hashKey(key);

  await db.insert(schema.apiKeys).values({
    id,
    name,
    scopes: JSON.stringify(scopes),
    prefix,
    hashedKey: hashed,
    createdAt: now,
    updatedAt: now,
    createdBy: user.email,
    expiresAt: expiresAt || null,
  });

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "create",
    resourceType: "api_key",
    resourceId: id,
    afterJson: JSON.stringify({ name, scopes, prefix, expiresAt }),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ id, key, name, scopes, prefix, createdAt: now, expiresAt }, 201);
});

settingsRoutes.delete("/api-keys/:id", async (c) => {
  const user = c.get("user");
  const id = c.req.param("id");
  const db = getDb(c.env);

  const existing = await db.select().from(schema.apiKeys).where(sql`${schema.apiKeys.id} = ${id}`).get();
  if (!existing) return c.json({ error: "Not found" }, 404);

  await db.delete(schema.apiKeys).where(sql`${schema.apiKeys.id} = ${id}`);

  await db.insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "delete",
    resourceType: "api_key",
    resourceId: id,
    beforeJson: JSON.stringify({ name: existing.name, prefix: existing.prefix }),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ success: true });
});

async function hashKey(key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, "0")).join("");
}

export { settingsRoutes };