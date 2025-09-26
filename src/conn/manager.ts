import { TikTokLiveConnection, WebcastEvent } from "tiktok-live-connector";
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

    // ★ options には session/IDC を渡さない（型エラー回避）
    const conn = new TikTokLiveConnection(uniqueId);

    // ★ 公式READMEの推奨どおり、後から CookieJar に設定
    //    connection.webClient.cookieJar.setSession('<sessionid>', '<tt-target-idc>')
    conn.webClient.cookieJar.setSession(
      this.cookies!.sessionid,
      this.cookies!["tt-target-idc"]
    ); // :contentReference[oaicite:2]{index=2}

    // 代表的イベント（必要に応じて）
    conn.on(WebcastEvent.CHAT, d => {
      // 例：ログ最小限
      // console.log(`[CHAT:${uniqueId}] ${d.user.uniqueId}: ${d.comment}`);
    });

    // ★ “disconnected” という生文字列は EventMap に無いので登録しない
    //   代わりに送信失敗や connect() 例外で自前リトライ（下記 send() 参照）

    await conn.connect();
    this.pool.set(uniqueId, conn);
  }

  async send(uniqueId: string, message: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (!conn) throw new Error(`Not connected to ${uniqueId}. Call /connect first.`);

    try {
      await conn.sendMessage(message); // 2.0.2+ でサポート :contentReference[oaicite:3]{index=3}
    } catch (err) {
      // 軽い再接続リトライ（型安全に依存しない実装）
      for (let i = 0; i < 3; i++) {
        try {
          await new Promise(r => setTimeout(r, 500 * (i + 1)));
          await conn.connect();
          await conn.sendMessage(message);
          return;
        } catch { /* 次のリトライへ */ }
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
