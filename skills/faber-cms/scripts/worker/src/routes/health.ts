import { Hono } from "hono";
import type { Env } from "../types";

const healthRoutes = new Hono<Env>();

healthRoutes.get("/", (c) => {
  return c.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    environment: c.env.ENVIRONMENT,
    version: "1.1.0",
  });
});

healthRoutes.get("/db", async (c) => {
  try {
    const db = c.env.DB;
    const result = await db.prepare("SELECT 1 as ok").first();
    return c.json({
      status: "ok",
      database: result?.ok === 1 ? "connected" : "error",
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return c.json({ status: "error", database: "disconnected", error: String(err) }, 500);
  }
});

healthRoutes.get("/kv", async (c) => {
  try {
    await c.env.SESSIONS.put("health-check", "ok", { expirationTtl: 60 });
    const value = await c.env.SESSIONS.get("health-check");
    return c.json({
      status: "ok",
      kv: value === "ok" ? "connected" : "error",
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return c.json({ status: "error", kv: "disconnected", error: String(err) }, 500);
  }
});

healthRoutes.get("/r2", async (c) => {
  try {
    const testKey = "health-check.txt";
    await c.env.MEDIA.put(testKey, "ok");
    const obj = await c.env.MEDIA.get(testKey);
    await c.env.MEDIA.delete(testKey);
    return c.json({
      status: "ok",
      r2: obj ? "connected" : "error",
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return c.json({ status: "error", r2: "disconnected", error: String(err) }, 500);
  }
});

export { healthRoutes };