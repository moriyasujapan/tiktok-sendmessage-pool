// src/server.ts
import express from "express";
import * as dotenv from "dotenv";
import pino from "pino";
import fs from "fs/promises";
import { fetchCookiesWithSelenium } from "./auth/selenium.js";
import { ConnectionManager } from "./conn/manager.js";

dotenv.config();

type CookieCache = { sessionid: string; "tt-target-idc": string };

const app = express();
const log = pino({ level: process.env.LOG_LEVEL ?? "info" });
app.use(express.json());

const COOKIE_PATH = process.env.COOKIE_CACHE_PATH ?? "./cookies.json";
const manager = new ConnectionManager();

let cookies: CookieCache | undefined;

/** cookies.json を読み込む */
async function loadCookies(): Promise<CookieCache> {
  const raw = await fs.readFile(COOKIE_PATH, "utf-8");
  return JSON.parse(raw) as CookieCache;
}

/** 起動時：Seleniumで自動ログイン→cookie保存→読込
 *  失敗したら既存 cookies.json を使う（無ければ終了）
 */
(async () => {
  try {
    log.info("Fetching TikTok cookies via Selenium...");
    await fetchCookiesWithSelenium(); // 成功すると COOKIE_PATH に保存される
    log.info("Cookies fetched.");
  } catch (e) {
    log.warn({ err: String(e) }, "Selenium cookie fetch FAILED. Trying cached cookies...");
    try {
      await fs.access(COOKIE_PATH);
      log.info("Using cached cookies.");
    } catch {
      log.error("No cookies available. Please login (manual) once.");
      process.exit(1);
    }
  }

  // 最終的な cookies をロード
  cookies = await loadCookies();
  if (!cookies.sessionid || !cookies["tt-target-idc"]) {
    log.error("cookies.json missing sessionid or tt-target-idc.");
    process.exit(1);
  }
  await manager.loadCookies(COOKIE_PATH);
})().catch((err) => {
  log.error({ err }, "Fatal at startup");
  process.exit(1);
});

/** ヘルスチェック */
app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

/** 常駐接続を作成（再利用用）
 * body: { uniqueId: string }
 */
app.post("/connect", async (req, res) => {
  const { uniqueId } = req.body ?? {};
  if (!uniqueId) return res.status(400).json({ error: "uniqueId is required" });
  if (!cookies) return res.status(500).json({ error: "cookies not loaded" });

  try {
    // 認証オプションは README 記載のとおり sessionId / ttTargetIdc
    await manager.connect(String(uniqueId), cookies.sessionid, cookies["tt-target-idc"]);
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

/** 送信（常駐コネクションを再利用）
 * body: { uniqueId: string, message: string }
 */
app.post("/send", async (req, res) => {
  const { uniqueId, message } = req.body ?? {};
  if (!uniqueId || !message) {
    return res.status(400).json({ error: "uniqueId and message are required" });
  }
  try {
    await manager.send(String(uniqueId), String(message)); // v2.0.2+ で sendMessage 対応
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

/** 切断
 * body: { uniqueId: string }
 */
app.post("/disconnect", async (req, res) => {
  const { uniqueId } = req.body ?? {};
  if (!uniqueId) return res.status(400).json({ error: "uniqueId is required" });
  try {
    await manager.disconnect(String(uniqueId));
    res.json({ ok: true });
  } catch (err: any) {
    res.status(500).json({ error: err?.message ?? String(err) });
  }
});

const port = Number(process.env.PORT ?? 3000);
const server = app.listen(port, () => log.info(`API listening on :${port}`));

process.on("SIGINT", async () => {
  log.info("Shutting down...");
  try {
    await manager.shutdownAll();
  } finally {
    server.close(() => process.exit(0));
  }
});
