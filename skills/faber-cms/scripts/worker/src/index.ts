import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { cfAccessMiddleware, requireRole } from "./middleware/cf-access";
import { healthRoutes } from "./routes/health";
import { collectionsRoutes } from "./routes/collections";
import { contentRoutes } from "./routes/content";
import { mediaRoutes } from "./routes/media";
import { settingsRoutes } from "./routes/settings";
import type { Env } from "./types";

const app = new Hono<Env>();

app.use("*", logger());
app.use("*", cors({
  origin: ["*"],
  allowHeaders: ["Content-Type", "Authorization", "Cf-Access-Jwt-Assertion"],
  allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  credentials: true,
}));

// Public routes
app.route("/health", healthRoutes);

// Protected routes (require CF Access)
app.use("/api/*", cfAccessMiddleware);

// Content routes (editor+ for write, viewer+ for read)
app.get("/api/content", contentRoutes);
app.get("/api/content/:id", contentRoutes);
app.post("/api/content", requireRole("admin", "editor"), contentRoutes);
app.put("/api/content/:id", requireRole("admin", "editor"), contentRoutes);
app.delete("/api/content/:id", requireRole("admin", "editor"), contentRoutes);
app.post("/api/content/:id/publish", requireRole("admin", "editor"), contentRoutes);
app.post("/api/content/:id/preview", requireRole("admin", "editor"), contentRoutes);

// Collections routes (admin only for write)
app.get("/api/collections", collectionsRoutes);
app.get("/api/collections/:name", collectionsRoutes);
app.post("/api/collections", requireRole("admin"), collectionsRoutes);
app.put("/api/collections/:name", requireRole("admin"), collectionsRoutes);
app.delete("/api/collections/:name", requireRole("admin"), collectionsRoutes);

// Media routes (editor+ for upload, viewer+ for read)
app.get("/api/media", mediaRoutes);
app.get("/api/media/:id", mediaRoutes);
app.post("/api/media/upload/init", requireRole("admin", "editor"), mediaRoutes);
app.post("/api/media/upload/complete", requireRole("admin", "editor"), mediaRoutes);
app.delete("/api/media/:id", requireRole("admin", "editor"), mediaRoutes);

// Settings routes (admin only)
app.get("/api/settings/site", settingsRoutes);
app.put("/api/settings/site", requireRole("admin"), settingsRoutes);
app.get("/api/settings/webhooks", requireRole("admin"), settingsRoutes);
app.post("/api/settings/webhooks", requireRole("admin"), settingsRoutes);
app.put("/api/settings/webhooks/:id", requireRole("admin"), settingsRoutes);
app.delete("/api/settings/webhooks/:id", requireRole("admin"), settingsRoutes);
app.get("/api/settings/api-keys", requireRole("admin"), settingsRoutes);
app.post("/api/settings/api-keys", requireRole("admin"), settingsRoutes);
app.delete("/api/settings/api-keys/:id", requireRole("admin"), settingsRoutes);

// Preview route (public, signed URL)
app.get("/preview/:collection/:slug", async (c) => {
  const token = c.req.query("t");
  if (!token) return c.json({ error: "Preview token required" }, 400);

  const { verifyPreviewToken, getPreviewContent } = await import("./utils/preview");
  const payload = await verifyPreviewToken(c.env, token);
  if (!payload) return c.json({ error: "Invalid or expired preview token" }, 401);

  const collection = c.req.param("collection");
  const slug = c.req.param("slug");

  const item = await getPreviewContent(c.env, collection, slug, token);
  if (!item) return c.json({ error: "Preview not found" }, 404);

  return c.json({
    ...item,
    data: JSON.parse(item.data),
    isPreview: true,
    previewExpires: payload.exp * 1000,
  });
});

// 404 handler
app.notFound((c) => c.json({ error: "Not found" }, 404));

// Error handler
app.onError((err, c) => {
  console.error("Unhandled error:", err);
  return c.json({ error: "Internal server error" }, 500);
});

export default app;