"""签名器 — 管理浏览器实例，提供 API 调用和页面操作"""
import time
from playwright.sync_api import sync_playwright
from utils.config import DEBUG, get_environment, Environment

import os as _os

def _find_chrome():
    """定位 Playwright 安装的 Chromium"""
    import glob
    base = _os.path.expanduser("~/AppData/Local/ms-playwright")
    if _os.path.exists(base):
        # 找最新版本的 chromium
        dirs = sorted(glob.glob(base + "/chromium-*"), reverse=True)
        for d in dirs:
            exe = d + "/chrome-win64/chrome.exe"
            if _os.path.exists(exe):
                return exe
    return None

CHROME_EXE = _find_chrome()


class Signer:
    def __init__(self, cookies):
        for c in cookies:
            if "sameSite" in c:
                del c["sameSite"]

        # 本地 + 调试模式用有头浏览器（避免风控登出），GitHub Action 用无头
        env = get_environment()
        headless = not (env == Environment.LOCAL and DEBUG)

        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(headless=headless)
        except Exception:
            if CHROME_EXE:
                self._browser = self._pw.chromium.launch(
                    headless=headless, executable_path=CHROME_EXE
                )
            else:
                raise
        ctx = self._browser.new_context()
        ctx.set_default_navigation_timeout(120000)
        ctx.set_default_timeout(120000)
        page = ctx.new_page()
        ctx.add_cookies(cookies)
        page.goto(
            "https://creator.douyin.com/creator-micro/data/following/chat",
            timeout=60000,
        )
        page.wait_for_timeout(5000)
        self.page = page
        self._headless = headless
        self._wait_for_login()

    def _check_login(self):
        """通过 user_token API 检测登录状态，返回 True 已登录 / False 未登录"""
        r = self.api_fetch(
            "GET", "/aweme/v1/creator/im/user_token/v2/",
            {"aid": "2906", "app_name": "aweme_creator_platform", "device_platform": "web"},
        )
        return r.get("status_code") == 0 and bool(r.get("user_id"))

    def _wait_for_login(self):
        """检测登录状态；本地有头模式下若未登录则等待用户手动登录"""
        if self._check_login():
            print("[Signer] 登录状态正常")
            return

        if self._headless:
            print("[Signer] 未登录，且当前为无头模式，无法等待人工登录")
            return

        print("[Signer] 检测到登录界面，请在浏览器窗口中完成登录...")
        for i in range(120):  # 最多等 10 分钟
            time.sleep(5)
            if self._check_login():
                print(f"[Signer] 登录成功（等待约 {(i+1)*5} 秒）")
                return
            if (i + 1) % 12 == 0:
                print(f"[Signer] 仍在等待登录...（已等待 {(i+1)*5} 秒）")
        print("[Signer] 等待登录超时，继续执行（可能失败）")

    def api_fetch(self, method, path, params=None, body=None):
        """通过浏览器内 fetch() 调用 API。仅用于不需要 a_bogus 的简单端点"""
        import urllib.parse
        url = "https://creator.douyin.com" + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        arg = {"method": method, "url": url, "body": body}
        js = """
        async (arg) => {
            const o = {method: arg.method, headers: {'Accept':'application/json'}, credentials: 'include'};
            if (arg.body) { o.body = JSON.stringify(arg.body); o.headers['Content-Type'] = 'application/json'; }
            const r = await fetch(arg.url, o);
            const t = await r.text();
            try { return JSON.parse(t); }
            catch (e) { return {_status: r.status, _text: t.substring(0,300)}; }
        }
        """
        return self.page.evaluate(js, arg)

    def close(self):
        self._browser.close()
        self._pw.stop()
