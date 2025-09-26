// src/conn/manager.ts
import { TikTokLiveConnection, WebcastEvent, ControlEvent } from "tiktok-live-connector";

export class ConnectionManager {
  private pool = new Map<string, TikTokLiveConnection>();

  async connect(uniqueId: string, sessionId: string, ttTargetIdc: string) {
    if (this.pool.has(uniqueId)) return;

    // READMEの認証オプション（sessionId / ttTargetIdc）をそのまま渡す
    const conn = new TikTokLiveConnection(uniqueId, { sessionId, ttTargetIdc });

    conn.on(WebcastEvent.CHAT, (d: any) => {
      // 必要ならログ
      // console.log(`[CHAT:${uniqueId}] ${d.user?.uniqueId}: ${d.comment}`);
    });

    conn.on(ControlEvent.DISCONNECTED, () => {
      // 必要なら監視・再接続
    });

    await conn.connect();
    this.pool.set(uniqueId, conn);
  }

  async send(uniqueId: string, message: string) {
    const conn = this.pool.get(uniqueId);
    if (!conn) throw new Error(`Not connected to ${uniqueId}`);
    await conn.sendMessage(message);
  }

  async disconnect(uniqueId: string) {
    const conn = this.pool.get(uniqueId);
    if (conn) {
      await conn.disconnect();
      this.pool.delete(uniqueId);
    }
  }
  async shutdownAll() {
    for (const [id, conn] of this.pool) {
      try { await conn.disconnect(); } catch {}
      this.pool.delete(id);
    }
  }
}
