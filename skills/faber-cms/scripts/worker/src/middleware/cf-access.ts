import { createMiddleware } from "hono/factory";
import { verify } from "hono/jwt";
import type { Env, CfAccessPayload, User } from "../types";
import { getDb } from "../db";

const JWKS_CACHE = new Map<string, { keys: any[]; expires: number }>();

async function fetchJwks(teamDomain: string): Promise<{ keys: any[] }> {
  const cached = JWKS_CACHE.get(teamDomain);
  if (cached && cached.expires > Date.now()) {
    return { keys: cached.keys };
  }

  const jwksUrl = `https://${teamDomain}/cdn-cgi/access/certs`;
  const response = await fetch(jwksUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch JWKS: ${response.status}`);
  }
  const jwks = await response.json();
  JWKS_CACHE.set(teamDomain, { keys: jwks.keys, expires: Date.now() + 3600000 });
  return jwks;
}

async function getUserRole(db: ReturnType<typeof getDb>, email: string): Promise<User["role"]> {
  const user = await db.select().from(schema.users).where(sql`${schema.users.email} = ${email}`).get();
  if (user) return user.role;

  // Default role for new users
  const defaultRole: User["role"] = "viewer";
  await db.insert(schema.users).values({
    email,
    role: defaultRole,
    name: email.split("@")[0],
    lastLogin: new Date().toISOString(),
  }).onConflictDoUpdate({
    target: schema.users.email,
    set: { lastLogin: new Date().toISOString() },
  });
  return defaultRole;
}

export const cfAccessMiddleware = createMiddleware<Env>(async (c, next) => {
  const teamDomain = c.env.CF_ACCESS_TEAM_DOMAIN;
  const expectedAud = c.env.CF_ACCESS_AUD.split(",").map((s) => s.trim());

  const jwt = c.req.header("Cf-Access-Jwt-Assertion");
  if (!jwt) {
    return c.json({ error: "Authentication required: Cf-Access-Jwt-Assertion header missing" }, 401);
  }

  try {
    const jwks = await fetchJwks(teamDomain);
    const payload = await verify(jwt, jwks.keys[0], "RS256") as unknown as CfAccessPayload;

    const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
    const validAud = aud.some((a) => expectedAud.includes(a));
    if (!validAud) {
      return c.json({ error: "Invalid audience" }, 403);
    }

    const email = payload.email || payload.sub;
    const db = getDb(c.env);
    const role = await getUserRole(db, email);

    c.set("user", { email, role, name: email.split("@")[0] });

    await next();
  } catch (err) {
    console.error("CF Access validation failed:", err);
    return c.json({ error: "Authentication failed" }, 401);
  }
});

export const requireRole = (...allowedRoles: User["role"][]) => {
  return createMiddleware<Env>(async (c, next) => {
    const user = c.get("user");
    if (!user || !allowedRoles.includes(user.role)) {
      return c.json({ error: "Insufficient permissions" }, 403);
    }
    await next();
  });
};