import { createHmac, timingSafeEqual } from "node:crypto";
import { handleUpload } from "@vercel/blob/client";

const COOKIE_NAME = "px_admin";

function cookieSecret() {
  const env = (process.env.PLAY_ADMIN_SECRET || "").trim();
  if (!env) throw new Error("PLAY_ADMIN_SECRET missing");
  return Buffer.from(env, "utf8");
}

function validateSessionCookie(raw) {
  if (!raw || raw.split("|").length !== 3) return false;
  const [status, expS, sig] = raw.split("|");
  const exp = Number(expS);
  if (status !== "ok" || !Number.isFinite(exp) || exp < Math.floor(Date.now() / 1000)) {
    return false;
  }
  const payload = `${status}|${exp}`;
  const expect = createHmac("sha256", cookieSecret()).update(payload).digest("hex");
  try {
    const a = Buffer.from(sig, "utf8");
    const b = Buffer.from(expect, "utf8");
    return a.length === b.length && timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

function readCookie(req, name) {
  const header = req.headers.get("cookie") || "";
  const parts = header.split(/;\s*/);
  for (const part of parts) {
    const i = part.indexOf("=");
    if (i === -1) continue;
    const k = part.slice(0, i).trim();
    if (k === name) return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

export async function POST(request) {
  try {
    if (!process.env.BLOB_READ_WRITE_TOKEN) {
      return Response.json({ error: "BLOB_READ_WRITE_TOKEN not configured" }, { status: 500 });
    }
    const cookie = readCookie(request, COOKIE_NAME);
    if (!validateSessionCookie(cookie)) {
      return Response.json({ error: "unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async () => ({
        allowedContentTypes: [
          "application/vnd.android.package-archive",
          "application/octet-stream",
          "application/zip",
          "image/png",
          "image/jpeg",
          "image/webp",
          "image/jpg",
        ],
        maximumSizeInBytes: 220 * 1024 * 1024,
        addRandomSuffix: true,
        tokenPayload: JSON.stringify({ role: "px-admin" }),
      }),
      onUploadCompleted: async () => {
        // Metadata is saved by FastAPI publish after client returns blob.url
      },
    });
    return Response.json(jsonResponse);
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "upload token failed" },
      { status: 400 },
    );
  }
}
