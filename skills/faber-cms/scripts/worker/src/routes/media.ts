import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { sql } from "drizzle-orm";
import { uuidv4 } from "../utils/crypto";
import type { Env } from "../types";
import { getDb, schema } from "../db";

const mediaRoutes = new Hono<Env>();

mediaRoutes.get("/", async (c) => {
  const limit = parseInt(c.req.query("limit") || "50");
  const offset = parseInt(c.req.query("offset") || "0");
  const mimeType = c.req.query("mime_type");

  let query = `SELECT * FROM media`;
  const params: any[] = [];

  if (mimeType) {
    query += " WHERE mime_type LIKE ?";
    params.push(mimeType + "%");
  }

  query += " ORDER BY uploaded_at DESC LIMIT ? OFFSET ?";
  params.push(limit, offset);

  const results = await c.env.DB.prepare(query).bind(...params).all();

  const totalQuery = mimeType
    ? "SELECT COUNT(*) as count FROM media WHERE mime_type LIKE ?"
    : "SELECT COUNT(*) as count FROM media";
  const totalParams = mimeType ? [mimeType + "%"] : [];
  const total = await c.env.DB.prepare(totalQuery).bind(...totalParams).first();

  return c.json({
    items: results.results,
    pagination: { limit, offset, total: total?.count || 0 },
  });
});

mediaRoutes.get("/:id", async (c) => {
  const id = c.req.param("id");
  const item = await c.env.DB.prepare("SELECT * FROM media WHERE id = ?").bind(id).first();
  if (!item) return c.json({ error: "Not found" }, 404);
  return c.json(item);
});

const uploadInitSchema = z.object({
  filename: z.string().min(1).max(256),
  mimeType: z.string().regex(/^(image|video|audio|application)\//),
  size: z.number().int().positive().max(50 * 1024 * 1024), // 50MB max
});

mediaRoutes.post("/upload/init", zValidator("json", uploadInitSchema), async (c) => {
  const { filename, mimeType, size } = c.req.valid("json");
  const user = c.get("user");
  const id = uuidv4();
  const ext = filename.split(".").pop() || "";
  const key = `uploads/${user.email}/${id}.${ext}`;

  const uploadUrl = await c.env.MEDIA.createPresignedUploadUrl(key, {
    expiresIn: 300, // 5 minutes
    contentType: mimeType,
    contentLength: size,
  });

  const now = new Date().toISOString();
  await c.env.DB.prepare(
    `INSERT INTO media (id, key, url, mime_type, size, metadata, uploaded_by, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, key, "", mimeType, size, JSON.stringify({ originalFilename: filename }), user.email, now).run();

  return c.json({ id, key, uploadUrl, expiresIn: 300 });
});

mediaRoutes.post("/upload/complete", zValidator("json", z.object({ id: z.string().uuid() })), async (c) => {
  const { id } = c.req.valid("json");
  const user = c.get("user");

  const item = await c.env.DB.prepare("SELECT * FROM media WHERE id = ? AND uploaded_by = ?").bind(id, user.email).first();
  if (!item) return c.json({ error: "Upload session not found" }, 404);

  const publicUrl = `${new URL(c.req.url).origin}/media/${item.key}`;
  const now = new Date().toISOString();

  await c.env.DB.prepare(
    `UPDATE media SET url = ?, metadata = json_set(metadata, '$.completed', true), uploaded_at = ? WHERE id = ?`
  ).bind(publicUrl, now, id).run();

  await getDb(c.env).insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "upload",
    resourceType: "media",
    resourceId: id,
    afterJson: JSON.stringify({ ...item, url: publicUrl, completed: true }),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ id, url: publicUrl, key: item.key });
});

mediaRoutes.delete("/:id", async (c) => {
  const id = c.req.param("id");
  const user = c.get("user");

  const item = await c.env.DB.prepare("SELECT * FROM media WHERE id = ?").bind(id).first();
  if (!item) return c.json({ error: "Not found" }, 404);

  await c.env.MEDIA.delete(item.key);
  await c.env.DB.prepare("DELETE FROM media WHERE id = ?").bind(id).run();

  await getDb(c.env).insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "delete",
    resourceType: "media",
    resourceId: id,
    beforeJson: JSON.stringify(item),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ success: true });
});

export { mediaRoutes };