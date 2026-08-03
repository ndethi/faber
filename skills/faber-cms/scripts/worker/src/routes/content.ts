import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { sql, eq, and, like, desc, count } from "drizzle-orm";
import { v4 as uuidv4 } from "uuid";
import type { Env, ContentEntry, PaginatedResponse } from "../types";
import { getDb, schema } from "../db";

const contentRoutes = new Hono<Env>();

const listQuerySchema = z.object({
  collection: z.string().min(1),
  status: z.enum(["draft", "published", "archived"]).optional().default("published"),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  offset: z.coerce.number().int().min(0).optional().default(0),
  search: z.string().optional(),
});

contentRoutes.get("/", zValidator("query", listQuerySchema), async (c) => {
  const { collection, status, limit, offset, search } = c.req.valid("query");
  const db = getDb(c.env);

  const tableName = `content_${collection}`;
  const contentTable = sqliteTable(tableName, {
    id: text("id").primaryKey(),
    collectionId: integer("collection_id").notNull(),
    version: integer("version").notNull().default(1),
    data: text("data").notNull(),
    status: text("status", { enum: ["draft", "published", "archived"] }).notNull().default("draft"),
    createdAt: text("created_at"),
    updatedAt: text("updated_at"),
    publishedAt: text("published_at"),
    createdBy: text("created_by"),
    updatedBy: text("updated_by"),
    slug: text("slug"),
  });

  let query = sql`SELECT * FROM ${sql.raw(tableName)} WHERE status = ${status}`;
  const params: any[] = [];

  if (search) {
    query = sql`${query} AND data LIKE ${"%" + search + "%"}`;
  }

  query = sql`${query} ORDER BY updated_at DESC LIMIT ${limit} OFFSET ${offset}`;

  const results = await c.env.DB.prepare(query as any).bind(...params).all();

  const totalResult = await c.env.DB.prepare(
    `SELECT COUNT(*) as count FROM ${tableName} WHERE status = ?`
  ).bind(status).first();

  return c.json({
    items: results.results,
    pagination: { limit, offset, total: totalResult?.count || 0 },
  } as PaginatedResponse<any>);
});

contentRoutes.get("/:id", async (c) => {
  const id = c.req.param("id");
  const collection = c.req.query("collection");
  if (!collection) return c.json({ error: "collection query param required" }, 400);

  const tableName = `content_${collection}`;
  const item = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  if (!item) return c.json({ error: "Not found" }, 404);
  return c.json(item);
});

const createContentSchema = z.object({
  collection: z.string().min(1),
  slug: z.string().min(1).max(256).optional(),
  data: z.record(z.any()),
  status: z.enum(["draft", "published", "archived"]).default("draft"),
});

contentRoutes.post("/", zValidator("json", createContentSchema), async (c) => {
  const { collection, slug, data, status } = c.req.valid("json");
  const user = c.get("user");
  const db = getDb(c.env);
  const now = new Date().toISOString();
  const id = uuidv4();

  const tableName = `content_${collection}`;

  const columns = ["id", "collection_id", "data", "status", "created_at", "updated_at", "created_by", "updated_by", "version"];
  const placeholders = ["?", "?", "?", "?", "?", "?", "?", "?", "?"];
  const values = [id, 1, JSON.stringify(data), status, now, now, user.email, user.email, 1];

  if (slug) {
    columns.push("slug");
    placeholders.push("?");
    values.push(slug);
  }

  if (status === "published") {
    columns.push("published_at");
    placeholders.push("?");
    values.push(now);
  }

  await c.env.DB.prepare(
    `INSERT INTO ${tableName} (${columns.join(", ")}) VALUES (${placeholders.join(", ")})`
  ).bind(...values).run();

  const newItem = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "create",
    resourceType: "content",
    resourceId: `${collection}/${id}`,
    afterJson: JSON.stringify(newItem),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  // Sync to Git if published
  if (status === "published" && c.env.GITHUB_TOKEN) {
    await syncToGit(c.env, collection, newItem);
  }

  return c.json(newItem, 201);
});

const updateContentSchema = z.object({
  collection: z.string().min(1),
  data: z.record(z.any()).optional(),
  status: z.enum(["draft", "published", "archived"]).optional(),
  slug: z.string().optional(),
});

contentRoutes.put("/:id", zValidator("json", updateContentSchema), async (c) => {
  const id = c.req.param("id");
  const { collection, data, status, slug } = c.req.valid("json");
  const user = c.get("user");
  const db = getDb(c.env);
  const now = new Date().toISOString();

  if (!data && !status && !slug) return c.json({ error: "No fields to update" }, 400);

  const tableName = `content_${collection}`;

  const existing = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  if (!existing) return c.json({ error: "Not found" }, 404);

  const updates = ["updated_at = ?", "updated_by = ?", "version = version + 1"];
  const params = [now, user.email];

  if (data) { updates.push("data = ?"); params.push(JSON.stringify(data)); }
  if (status) {
    updates.push("status = ?"); params.push(status);
    if (status === "published") {
      updates.push("published_at = ?"); params.push(now);
    }
  }
  if (slug) { updates.push("slug = ?"); params.push(slug); }

  params.push(id);

  await c.env.DB.prepare(
    `UPDATE ${tableName} SET ${updates.join(", ")} WHERE id = ?`
  ).bind(...params).run();

  const updated = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "update",
    resourceType: "content",
    resourceId: `${collection}/${id}`,
    beforeJson: JSON.stringify(existing),
    afterJson: JSON.stringify(updated),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  // Sync to Git if published
  if (status === "published" && c.env.GITHUB_TOKEN) {
    await syncToGit(c.env, collection, updated!);
  }

  return c.json(updated);
});

contentRoutes.delete("/:id", async (c) => {
  const id = c.req.param("id");
  const collection = c.req.query("collection");
  if (!collection) return c.json({ error: "collection query param required" }, 400);

  const user = c.get("user");
  const db = getDb(c.env);
  const tableName = `content_${collection}`;

  const existing = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  if (!existing) return c.json({ error: "Not found" }, 404);

  await c.env.DB.prepare(
    `UPDATE ${tableName} SET status = 'archived', updated_at = ? WHERE id = ?`
  ).bind(new Date().toISOString(), id).run();

  await db.insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "archive",
    resourceType: "content",
    resourceId: `${collection}/${id}`,
    beforeJson: JSON.stringify(existing),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ success: true });
});

contentRoutes.post("/:id/publish", async (c) => {
  const id = c.req.param("id");
  const collection = c.req.query("collection");
  if (!collection) return c.json({ error: "collection query param required" }, 400);

  const user = c.get("user");
  const db = getDb(c.env);
  const tableName = `content_${collection}`;
  const now = new Date().toISOString();

  const existing = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  if (!existing) return c.json({ error: "Not found" }, 404);

  await c.env.DB.prepare(
    `UPDATE ${tableName} SET status = 'published', published_at = ?, updated_at = ?, updated_by = ?, version = version + 1 WHERE id = ?`
  ).bind(now, now, user.email, id).run();

  const updated = await c.env.DB.prepare(
    `SELECT * FROM ${tableName} WHERE id = ?`
  ).bind(id).first();

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "publish",
    resourceType: "content",
    resourceId: `${collection}/${id}`,
    beforeJson: JSON.stringify(existing),
    afterJson: JSON.stringify(updated),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  if (c.env.GITHUB_TOKEN) {
    await syncToGit(c.env, collection, updated!);
  }

  return c.json(updated);
});

contentRoutes.post("/:id/preview", async (c) => {
  const id = c.req.param("id");
  const collection = c.req.query("collection");
  if (!collection) return c.json({ error: "collection query param required" }, 400);

  const item = await c.env.DB.prepare(
    `SELECT * FROM content_${collection} WHERE id = ?`
  ).bind(id).first();

  if (!item) return c.json({ error: "Not found" }, 404);

  const { createPreviewURL } = await import("../utils/preview");
  const previewUrl = await createPreviewURL(c.env, {
    id: item.id,
    version: item.version,
    collection: item.collection as any,
    slug: item.slug as any,
    data: item.data as any,
    status: item.status as any,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    publishedAt: item.published_at,
    createdBy: item.created_by,
    updatedBy: item.updated_by,
  });

  return c.json({ previewUrl, expiresIn: 3600 });
});

async function syncToGit(env: Env, collection: string, content: any) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO) return;

  const frontmatter = extractFrontmatter(content.data);
  const body = extractBody(content.data);
  const filePath = `src/content/${collection}/${content.slug}.md`;

  const octokitResponse = await fetch(
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${filePath}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github.v3+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: `cms: publish ${collection}/${content.slug}`,
        content: Buffer.from(frontmatter + "\n" + body).toString("base64"),
        branch: "main",
      }),
    }
  );

  if (!octokitResponse.ok) {
    console.error("GitHub sync failed:", await octokitResponse.text());
  }
}

function extractFrontmatter(data: string): string {
  const parsed = JSON.parse(data);
  const { body, ...frontmatter } = parsed;
  return "---\n" + Object.entries(frontmatter)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join("\n") + "\n---";
}

function extractBody(data: string): string {
  return JSON.parse(data).body || "";
}

export { contentRoutes };