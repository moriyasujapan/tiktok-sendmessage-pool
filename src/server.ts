import express from "express";
import * as dotenv from "dotenv";
import pino from "pino";
import { fetchCookiesWithSelenium } from "./auth/selenium.js";
import { ConnectionManager } from "./conn/manager.js";
import fs from "fs/promises";

dotenv.config();
const app = express();
const log = pino({ level: process.env.LOG_LEVEL ?? "info" });
app.use(express.json());

// 起動時：クッキー取得 → プール読込み
(async () => {
  try {
    log.info("Fetching TikTok cookies via Selenium...");
    await fetchCookiesWithSelenium();
    log.info("Cookies fetched.");
  } catch (e) {
    log.warn({ err: String(e) }, "Selenium cookie fetch FAILED. Trying cached cookies...");
    try {
      const cachePath = process.env.COOKIE_CACHE_PATH ?? "./cookies.json";
      await fs.access(cachePath);
      log.info("Using cached cookies.");
    } catch {
      log.error("No cookies available. Please login (manual) once.");
      process.exit(1);
    }
  }
  await ConnectionManager.instance.loadCookies();
})().catch(err => {
  log.error({ err }, "Fatal at startup");
  process.exit(1);
});

app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/connect", async (req, res) => {
  const { uniqueId } = req.body ?? {};
  if (!uniqueId) return res.status(400).json({ error: "uniqueId is required" });
  try {
    await ConnectionManager.instance.connect(String(uniqueId));
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

app.post("/send", async (req, res) => {
  const { uniqueId, message } = req.body ?? {};
  if (!uniqueId || !message) return res.status(400).json({ error: "uniqueId and message are required" });
  try {
    await ConnectionManager.instance.send(String(uniqueId), String(message));
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

app.post("/disconnect", async (req, res) => {
  const { uniqueId } = req.body ?? {};
  if (!uniqueId) return res.status(400).json({ error: "uniqueId is required" });
  try {
    await ConnectionManager.instance.disconnect(String(uniqueId));
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

const port = Number(process.env.PORT ?? 3000);
const server = app.listen(port, () => log.info(`API listening on :${port}`));

process.on("SIGINT", async () => {
  log.info("Shutting down...");
  await ConnectionManager.instance.shutdownAll();
  server.close(() => process.exit(0));
});

