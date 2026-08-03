import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { sql } from "drizzle-orm";
import type { Env } from "../types";
import { getDb, schema } from "../db";

const collectionsRoutes = new Hono<Env>();

collectionsRoutes.get("/", async (c) => {
  const db = getDb(c.env);
  const allCollections = await db.select().from(schema.collections).all();
  return c.json({ collections: allCollections });
});

collectionsRoutes.get("/:name", async (c) => {
  const name = c.req.param("name");
  const db = getDb(c.env);
  const collection = await db.select().from(schema.collections).where(sql`${schema.collections.name} = ${name}`).get();
  if (!collection) return c.json({ error: "Collection not found" }, 404);
  return c.json(collection);
});

const createCollectionSchema = z.object({
  name: z.string().min(1).max(64).regex(/^[a-z_][a-z0-9_]*$/),
  schema: z.record(z.any()),
  uiConfig: z.record(z.any()).optional().default({}),
});

collectionsRoutes.post("/", zValidator("json", createCollectionSchema), async (c) => {
  const { name, schema: zodSchema, uiConfig } = c.req.valid("json");
  const user = c.get("user");
  const db = getDb(c.env);

  const existing = await db.select().from(schema.collections).where(sql`${schema.collections.name} = ${name}`).get();
  if (existing) return c.json({ error: "Collection already exists" }, 409);

  const now = new Date().toISOString();
  await db.insert(schema.collections).values({
    name,
    schema: JSON.stringify(zodSchema),
    uiConfig: JSON.stringify(uiConfig),
    createdAt: now,
    updatedAt: now,
  });

  await db.insert(schema.auditLog).values({
    timestamp: now,
    userEmail: user.email,
    action: "create",
    resourceType: "collection",
    resourceId: name,
    afterJson: JSON.stringify({ name, schema: zodSchema, uiConfig }),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ name, schema: zodSchema, uiConfig }, 201);
});

const updateCollectionSchema = z.object({
  schema: z.record(z.any()).optional(),
  uiConfig: z.record(z.any()).optional(),
});

collectionsRoutes.put("/:name", zValidator("json", updateCollectionSchema), async (c) => {
  const name = c.req.param("name");
  const { schema: zodSchema, uiConfig } = c.req.valid("json");
  const user = c.get("user");
  const db = getDb(c.env);

  const existing = await db.select().from(schema.collections).where(sql`${schema.collections.name} = ${name}`).get();
  if (!existing) return c.json({ error: "Collection not found" }, 404);

  const updates: Record<string, any> = { updatedAt: new Date().toISOString() };
  if (zodSchema) updates.schema = JSON.stringify(zodSchema);
  if (uiConfig) updates.uiConfig = JSON.stringify(uiConfig);

  await db.update(schema.collections).set(updates).where(sql`${schema.collections.name} = ${name}`);

  const updated = await db.select().from(schema.collections).where(sql`${schema.collections.name} = ${name}`).get();

  await db.insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "update",
    resourceType: "collection",
    resourceId: name,
    beforeJson: JSON.stringify(existing),
    afterJson: JSON.stringify(updated),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json(updated);
});

collectionsRoutes.delete("/:name", async (c) => {
  const name = c.req.param("name");
  const user = c.get("user");
  const db = getDb(c.env);

  const existing = await db.select().from(schema.collections).where(sql`${schema.collections.name} = ${name}`).get();
  if (!existing) return c.json({ error: "Collection not found" }, 404);

  await db.delete(schema.collections).where(sql`${schema.collections.name} = ${name}`);

  await db.insert(schema.auditLog).values({
    timestamp: new Date().toISOString(),
    userEmail: user.email,
    action: "delete",
    resourceType: "collection",
    resourceId: name,
    beforeJson: JSON.stringify(existing),
    ip: c.req.header("cf-connecting-ip"),
    userAgent: c.req.header("user-agent"),
  });

  return c.json({ success: true });
});

export { collectionsRoutes };