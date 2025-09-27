import fs from "fs/promises";
import { Builder, By, until, WebDriver } from "selenium-webdriver";
import * as chrome from "selenium-webdriver/chrome.js";
import * as dotenv from "dotenv";
dotenv.config();

type Cookies = { sessionid: string; "tt-target-idc": string };

const LOGIN_URL = "https://www.tiktok.com/login";
const HOMEPAGE = "https://www.tiktok.com/";

export async function fetchCookiesWithSelenium(): Promise<Cookies> {
  const remoteUrl = process.env.SELENIUM_REMOTE_URL;
  const headless = (process.env.SELENIUM_HEADLESS ?? "false") === "true";

  const options = new chrome.Options();
  if (headless) 
    options.addArguments("--headless=new");
  options.addArguments("--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled");

  options.setUserPreferences({}); // placeholder if needed
  // options.setChromeBinaryPath(undefined); // 必要なら指定
  options.addArguments(`--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36`);
  options.excludeSwitches("enable-automation");
  options.add_experimental_option("excludeSwitches", ["enable-automation"])
  options.excludeSwitches("enable-automation", "load-extension");

  // ★ driver を nullable にしない
  let driver: WebDriver | undefined;
  try {
    driver = await new Builder()
      .forBrowser("chrome")
      .setChromeOptions(options)
      .usingServer(remoteUrl ?? "")
      .build();
    try {
      // CDP 経由でページ読み込み前に navigator.webdriver を上書きするスクリプトを登録
      // Chrome DevTools Protocol の Page.addScriptToEvaluateOnNewDocument を使う
      // NOTE: selenium-webdriver の Node バインディングでの CDP 呼び出し API はバージョンにより異なります。
      // ここでは低レベルの executeCdpCommand を想定した呼び出し例を示します（Selenium 4+）。
      const source = `
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined,
        });
        // 追加で plugins / languages の簡易偽装も入れられる
        Object.defineProperty(navigator, 'plugins', { get: () => [{name:'Chrome PDF Plugin'}] });
        Object.defineProperty(navigator, 'languages', { get: () => ['ja-JP','ja'] });
      `;
      // 実際の呼び出しは selenium のバージョンで差があるため try/catch でフォールバック
      try {
        // @ts-ignore: executeCdpCommand may not exist on the type depending on version
        await (driver as any).executeCdpCommand('Page.addScriptToEvaluateOnNewDocument', { source });
      } catch (e) {
        // selenium バージョンによっては別 API（sendDevToolsCommand 等）があるので試す
        try {
          // @ts-ignore
          await (driver as any).sendDevToolsCommand('Page.addScriptToEvaluateOnNewDocument', { source });
        } catch (err) {
          console.warn('CDP injection failed — your selenium binding may not support executeCdpCommand/sendDevToolsCommand in this version.', err);
        }
      }
    } catch (err) {
      console.warn('CDP injection failed — your selenium binding may not support executeCdpCommand/sendDevToolsCommand in this version.', err);
    }

    // 以降は driver! で明示（または if(!driver) throw）
    await driver!.get(LOGIN_URL);
    const webdriverFlag = await driver.executeScript('return navigator.webdriver');
    console.log('navigator.webdriver ->', webdriverFlag);

    const mode = (process.env.TIKTOK_LOGIN_MODE ?? "manual").toLowerCase();

    if (mode === "credentials") {
      await driver!.wait(until.elementLocated(By.css("input[type='text'],input[type='email']")), 15000);
      const userInput = await driver!.findElement(By.css("input[type='text'],input[type='email']"));
      await userInput.clear();
      await userInput.sendKeys(process.env.TIKTOK_USERNAME ?? "");

      await driver!.wait(until.elementLocated(By.css("input[type='password']")), 10000);
      const passInput = await driver!.findElement(By.css("input[type='password']"));
      await passInput.clear();
      await passInput.sendKeys(process.env.TIKTOK_PASSWORD ?? "");

      const submit = await driver!.findElements(By.css("button[type='submit'],button[data-e2e='login-button']"));
      if (submit[0]) await submit[0].click();

      await driver!.wait(async () => {
        await driver!.get(HOMEPAGE);
        const cookies = await driver!.manage().getCookies();
        return cookies.some((c: { name: string }) => c.name === "sessionid");
      }, 60000);
    } else {
      await driver!.wait(async () => {
        const cookies = await driver!.manage().getCookies();
        return cookies.some((c: { name: string }) => c.name === "sessionid");
      }, 300000);
      await driver!.get(HOMEPAGE);
    }

    const cookies = await driver!.manage().getCookies();
    const session = cookies.find((c: { name: string; value: string }) => c.name === "sessionid");
    const idc = cookies.find((c: { name: string; value: string }) => c.name === "tt-target-idc");

    if (!session || !idc) {
      throw new Error("Required cookies not found (sessionid / tt-target-idc).");
    }

    const result: Cookies = { sessionid: session.value, "tt-target-idc": idc.value };

    const cachePath = process.env.COOKIE_CACHE_PATH ?? "./cookies.json";
    await fs.writeFile(cachePath, JSON.stringify(result, null, 2), "utf-8");

    return result;
  } finally {
    if (driver) await driver.quit();
  }
}
