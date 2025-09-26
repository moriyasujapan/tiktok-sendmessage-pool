// 両系統（v1.2.x / v2.x）を吸収する薄い互換レイヤ
// - v1: WebcastPushConnection / 文字列イベント / sendMessage(text, sessionId?)
// - v2: TikTokLiveConnection   / 列挙イベント   / sendMessage(text) + 認証は options

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore: 型は版差異が大きいので any 扱いに寄せる
import * as TLC from "tiktok-live-connector";

export const TikTokLiveConnectionCompat: any =
  (TLC as any).TikTokLiveConnection ?? (TLC as any).WebcastPushConnection;

export const WebcastEventCompat: any =
  (TLC as any).WebcastEvent ?? {
    CHAT: "chat",
    GIFT: "gift",
    FOLLOW: "follow",
    // 必要に応じて追記
  };

export const ControlEventCompat: any =
  (TLC as any).ControlEvent ?? {
    DISCONNECTED: "disconnected",
    STREAM_END: "streamEnd",
    // 必要に応じて追記
  };

// v1 と v2 で “認証の渡し方” が違うため、統一ヘルパを用意
export function createAuthedConnection(uniqueId: string, cookies: {
  sessionid: string;
  "tt-target-idc"?: string; // v1 は未使用、v2 で利用
}) {
  // v2（TikTokLiveConnection）なら options に sessionId/ttTargetIdc を渡す
  if ((TLC as any).TikTokLiveConnection) {
    return new (TLC as any).TikTokLiveConnection(uniqueId, {
      sessionId: cookies.sessionid,
      ttTargetIdc: cookies["tt-target-idc"] ?? null
    });
  }

  // v1（WebcastPushConnection）なら constructor options に sessionId のみ
  return new (TLC as any).WebcastPushConnection(uniqueId, {
    sessionId: cookies.sessionid
  });
}

// v1/v2 の sendMessage 差異も吸収
export async function sendMessageCompat(conn: any, text: string, cookies?: {
  sessionid: string;
}) {
  if (typeof conn.sendMessage !== "function") {
    throw new Error("sendMessage is not available on this connector instance.");
  }
  // v1 は sendMessage(text, sessionId?)、v2 は sendMessage(text)
  try {
    if (conn.constructor?.name === "WebcastPushConnection") {
      return await conn.sendMessage(text, cookies?.sessionid);
    }
    return await conn.sendMessage(text);
  } catch (e) {
    throw e;
  }
}
