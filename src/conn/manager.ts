import { TikTokLiveConnection, WebcastEvent, ControlEvent } from "tiktok-live-connector";

export class ConnectionManager {
  private pool = new Map<string, TikTokLiveConnection>();

  async connect(uniqueId: string, sessionId: string, ttTargetIdc: string) {
    if (this.pool.has(uniqueId)) return;

    const conn = new TikTokLiveConnection(uniqueId, {
      sessionId,
      ttTargetIdc,
    });

    // イベントは列挙型で
    conn.on(WebcastEvent.CHAT, (d: any) => {
      // console.log(`[CHAT:${uniqueId}] ${d.user?.uniqueId}: ${d.comment}`);
    });
    conn.on(ControlEvent.DISCONNECTED, () => {
      // 再接続ロジックを必要ならここに
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
}
