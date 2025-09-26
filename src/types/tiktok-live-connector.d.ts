// 宣言マージで不足プロパティを足す
declare module 'tiktok-live-connector' {
  interface TikTokLiveConnectionOptions {
    /** TikTokの sessionid クッキー */
    sessionId?: string | null;
    /** TikTokの tt-target-idc クッキー（地域IDC） */
    ttTargetIdc?: string | null;
  }
}
