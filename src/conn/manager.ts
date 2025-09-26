import { TikTokLiveConnection } from "tiktok-live-connector";
import fs from "fs/promises";

type CookieCache = { sessionid: string; "tt-target-idc": string };

export class ConnectionManager {
  private static _instance: ConnectionManager;
  private pool: Map<string, TikTokLiveConnection> = new Map();
  private cookies?: CookieCache;

  static get instance(): ConnectionManager {
    if (!this._instance) this._instance = new ConnectionManager();
    return this._instance;
  }

  async loadCookies(path = process.env.COOKIE_CACHE_PATH ?? "./cookies.json") {
    const raw = await fs.readFile(path, "utf-8");
    this.cookies = JSON.parse(raw);
  }

  private ensureCookiesLoaded() {
    if (!this.cookies) throw new Error("Cookies not loaded. Call loadCookies() first.");
  }

  async connect(uniqueId: string): Promise<void> {
    this.ensureCookiesLoaded();
    if (this.pool.has(uniqueId)) return; // already connected

    const conn = new TikTokLiveConnection(uniqueId, {
      sessionId: this.cookies!.sessionid,
      ttTargetIdc: this.cookies!["tt-target-idc"]
    });

    // auto-reconnect on disconnect
    conn.on("disconnected", async () => {
      for (let i = 0; i < 5; i++) {
        try {
          await new Promise(r => setTimeout(r, 1000 * (i + 1)));
          await conn.connect();
          break;
        } catch {
          // リトライ
        }
      }
    });

    await conn.connect();
    this.pool.set(uniqueId, conn);
  }

  async send(uniqueId: string, message: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (!conn) throw new Error(`Not connected to ${uniqueId}. Call /connect first.`);
    await conn.sendMessage(message);
  }

  async disconnect(uniqueId: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (conn) {
      await conn.disconnect();
      this.pool.delete(uniqueId);
    }
  }

  async shutdownAll(): Promise<void> {
    for (const [id, conn] of this.pool.entries()) {
      try { await conn.disconnect(); } catch {}
      this.pool.delete(id);
    }
  }
}

