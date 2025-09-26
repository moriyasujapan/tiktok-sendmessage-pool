import fs from "fs/promises";
import {
  TikTokLiveConnectionCompat,
  WebcastEventCompat,
  ControlEventCompat,
  createAuthedConnection,
  sendMessageCompat
} from "./compat.js";

type CookieCache = { sessionid: string; "tt-target-idc"?: string };

export class ConnectionManager {
  private pool = new Map<string, any>();
  private cookies?: CookieCache;

  async loadCookies(path = process.env.COOKIE_CACHE_PATH ?? "./cookies.json") {
    const raw = await fs.readFile(path, "utf-8");
    this.cookies = JSON.parse(raw);
  }

  private ensureCookiesLoaded() {
    if (!this.cookies?.sessionid) throw new Error("Cookies not loaded");
  }

  async connect(uniqueId: string): Promise<void> {
    this.ensureCookiesLoaded();
    if (this.pool.has(uniqueId)) return;

    // ★ 版差異を吸収したユニファイド生成
    const conn = createAuthedConnection(uniqueId, this.cookies!);

    // イベント（列挙がある版は列挙、旧版は文字列にフォールバック）
    conn.on?.(WebcastEventCompat.CHAT, (d: any) => {
      // 必要ならログ
      // console.log(`[CHAT:${uniqueId}] ${d?.user?.uniqueId}: ${d?.comment}`);
    });

    conn.on?.(ControlEventCompat.DISCONNECTED, () => {
      // console.warn(`[${uniqueId}] disconnected`);
    });

    await conn.connect();
    this.pool.set(uniqueId, conn);
  }

  async send(uniqueId: string, message: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (!conn) throw new Error(`Not connected to ${uniqueId}`);
    await sendMessageCompat(conn, message, { sessionid: this.cookies!.sessionid });
  }

  async disconnect(uniqueId: string): Promise<void> {
    const conn = this.pool.get(uniqueId);
    if (conn) {
      await conn.disconnect?.();
      this.pool.delete(uniqueId);
    }
  }

  async shutdownAll(): Promise<void> {
    for (const [id, conn] of this.pool.entries()) {
      try { await conn.disconnect?.(); } catch {}
      this.pool.delete(id);
    }
  }
}
