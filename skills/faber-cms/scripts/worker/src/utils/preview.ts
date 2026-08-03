import { SignJWT, jwtVerify } from "jose";
import type { Env, PreviewPayload } from "../types";

const PREVIEW_TTL = 3600000; // 1 hour

export async function createPreviewURL(env: Env, content: {
  id: string;
  version: number;
  collection: string;
  slug: string;
}): Promise<string> {
  const secret = new TextEncoder().encode(env.PREVIEW_SECRET);
  const payload: PreviewPayload = {
    id: content.id,
    version: content.version,
    exp: Math.floor((Date.now() + PREVIEW_TTL) / 1000),
  };

  const token = await new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(Math.floor((Date.now() + PREVIEW_TTL) / 1000))
    .sign(secret);

  return `${env.PREVIEW_BASE}/preview/${content.collection}/${content.slug}?t=${token}`;
}

export async function verifyPreviewToken(env: Env, token: string): Promise<PreviewPayload | null> {
  try {
    const secret = new TextEncoder().encode(env.PREVIEW_SECRET);
    const { payload } = await jwtVerify(token, secret);
    return payload as unknown as PreviewPayload;
  } catch {
    return null;
  }
}

export async function getPreviewContent(env: Env, collection: string, slug: string, token: string) {
  const payload = await verifyPreviewToken(env, token);
  if (!payload) return null;

  const item = await env.DB.prepare(
    `SELECT * FROM content_${collection} WHERE id = ? AND version = ?`
  ).bind(payload.id, payload.version).first();

  if (!item) return null;
  if (item.status === "archived") return null;

  return item;
}