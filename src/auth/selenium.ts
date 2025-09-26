import fs from "fs/promises";
import { Builder, By, until, WebDriver } from "selenium-webdriver";
import chrome from "selenium-webdriver/chrome";
import * as dotenv from "dotenv";
dotenv.config();

type Cookies = { sessionid: string; "tt-target-idc": string };

const LOGIN_URL = "https://www.tiktok.com/login";
const HOMEPAGE = "https://www.tiktok.com/";

export async function fetchCookiesWithSelenium(): Promise<Cookies> {
  const remoteUrl = process.env.SELENIUM_REMOTE_URL;
  const headless = (process.env.SELENIUM_HEADLESS ?? "false") === "true";

  const options = new chrome.Options();
  if (headless) options.addArguments("--headless=new");
  options.addArguments("--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage");

  let driver: WebDriver | null = null;
  try {
    driver = await new Builder()
      .forBrowser("chrome")
      .setChromeOptions(options)
      .usingServer(remoteUrl ?? "")
      .build();

    await driver.get(LOGIN_URL);

    const mode = (process.env.TIKTOK_LOGIN_MODE ?? "manual").toLowerCase();

    if (mode === "credentials") {
      await driver.wait(until.elementLocated(By.css("input[type='text'],input[type='email']")), 15000);
      const userInput = await driver.findElement(By.css("input[type='text'],input[type='email']"));
      await userInput.clear();
      await userInput.sendKeys(process.env.TIKTOK_USERNAME ?? "");

      await driver.wait(until.elementLocated(By.css("input[type='password']")), 10000);
      const passInput = await driver.findElement(By.css("input[type='password']"));
      await passInput.clear();
      await passInput.sendKeys(process.env.TIKTOK_PASSWORD ?? "");

      const submit = await driver.findElements(By.css("button[type='submit'],button[data-e2e='login-button']"));
      if (submit[0]) await submit[0].click();

      await driver.wait(async () => {
        await driver.get(HOMEPAGE);
        const cookies = await driver.manage().getCookies();
        return cookies.some(c => c.name === "sessionid");
      }, 60000);
    } else {
      await driver.wait(async () => {
        const cookies = await driver.manage().getCookies();
        return cookies.some((c: { name: string }) => c.name === "sessionid");  // ★ 型注釈
      }, 300000);
      await driver.get(HOMEPAGE);
    }

    const cookies = await driver.manage().getCookies();
    const session = cookies.find((c: { name: string }) => c.name === "sessionid");     // ★ 型注釈
    const idc = cookies.find((c: { name: string }) => c.name === "tt-target-idc");     // ★ 型注釈

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

