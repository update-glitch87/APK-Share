import { createHmac, timingSafeEqual } from "node:crypto";
import express from "express";
import { handleUpload } from "@vercel/blob/client";

const COOKIE_NAME = "px_admin";
const app = express();
app.use(express.json({ limit: "2mb" }));

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
  const header = req.headers.cookie || "";
  const parts = header.split(/;\s*/);
  for (const part of parts) {
    const i = part.indexOf("=");
    if (i === -1) continue;
    const k = part.slice(0, i).trim();
    if (k === name) return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "blob" });
});

async function blobUploadHandler(req, res) {
  try {
    if (!process.env.BLOB_READ_WRITE_TOKEN) {
      return res.status(500).json({ error: "BLOB_READ_WRITE_TOKEN not configured" });
    }
    const cookie = readCookie(req, COOKIE_NAME);
    if (!validateSessionCookie(cookie)) {
      return res.status(401).json({ error: "unauthorized" });
    }

    // Adapt Express req into Fetch Request for handleUpload
    const request = new Request("http://local/api/blob-upload", {
      method: "POST",
      headers: { "content-type": "application/json", cookie: req.headers.cookie || "" },
      body: JSON.stringify(req.body || {}),
    });

    const jsonResponse = await handleUpload({
      body: req.body,
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
      onUploadCompleted: async () => {},
    });
    return res.json(jsonResponse);
  } catch (error) {
    return res.status(400).json({
      error: error instanceof Error ? error.message : "upload token failed",
    });
  }
}

app.post("/api/blob-upload", blobUploadHandler);
app.post("/", blobUploadHandler);

export default app;
