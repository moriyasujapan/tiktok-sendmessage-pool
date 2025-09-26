import { TikTokLiveConnection, WebcastEvent, ControlEvent } from "tiktok-live-connector";
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

    // ★ v2 README準拠: コンストラクタの options に sessionId / ttTargetIdc を渡す
    const conn = new TikTokLiveConnection(uniqueId, {
      sessionId: this.cookies!.sessionid,
      ttTargetIdc: this.cookies!["tt-target-idc"]
    });

    // 代表的イベント（必要ならログ出力を追加
    conn.on(WebcastEvent.CHAT, d => {
      // console.log(`[CHAT:${uniqueId}] ${d.user.uniqueId}: ${d.comment}`);
    });

    // ★ 切断は列挙で
    conn.on(ControlEvent.DISCONNECTED, () => {
      // 必要ならここで監視・再接続トリガ
      // console.warn(`[${uniqueId}] disconnected`);
    });

    await conn.connect();
    this.pool.set(uniqueId, conn);
  }

  async send(uniqueId: string, message: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (!conn) throw new Error(`Not connected to ${uniqueId}. Call /connect first.`);

    try {
      await conn.sendMessage(message); // v2.0.2+ で対応
    } catch (err) {
      // 軽い再接続リトライ
      for (let i = 0; i < 3; i++) {
        try {
          await new Promise(r => setTimeout(r, 500 * (i + 1)));
          await conn.connect();
          await conn.sendMessage(message);
          return;
        } catch { /* retry */ }
      }
      throw err;
    }
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
