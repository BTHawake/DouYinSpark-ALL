"""登录助手 — 有头模式打开抖音，等用户手动登录后自动提取 cookies"""
import json
import time
from playwright.sync_api import sync_playwright

import os as _os


def _find_chrome():
    import glob
    base = _os.path.expanduser("~/AppData/Local/ms-playwright")
    if _os.path.exists(base):
        dirs = sorted(glob.glob(base + "/chromium-*"), reverse=True)
        for d in dirs:
            exe = d + "/chrome-win64/chrome.exe"
            if _os.path.exists(exe):
                return exe
    return None


CHROME_EXE = _find_chrome()

print("正在打开抖音创作者中心（有头模式）...")
print("请在浏览器窗口里登录抖音，登录成功后我会自动保存 cookies")

pw = sync_playwright().start()
try:
    browser = pw.chromium.launch(headless=False, executable_path=CHROME_EXE)
except Exception:
    browser = pw.chromium.launch(headless=False)

ctx = browser.new_context(viewport={"width": 1280, "height": 800})
page = ctx.new_page()
page.goto("https://creator.douyin.com/", timeout=60000)

# 等待用户登录（轮询检查）
print("\n等待登录中...")
logged_in = False
for i in range(60):  # 最多等 5 分钟
    time.sleep(5)
    # 通过页面内 fetch 检查登录状态
    try:
        status = page.evaluate("""
        async () => {
            const r = await fetch('/aweme/v1/creator/im/user_token/v2/?aid=2906&app_name=aweme_creator_platform&device_platform=web', {credentials: 'include'});
            const d = await r.json();
            return d.status_code === 0 && d.user_id;
        }
        """)
        if status:
            logged_in = True
            break
    except Exception:
        pass
    if (i + 1) % 6 == 0:
        print(f"  已等待 {(i+1)*5} 秒...")

if not logged_in:
    print("超时未检测到登录，请手动重新运行本脚本")
    browser.close()
    pw.stop()
    exit(1)

print("检测到登录成功！正在提取 cookies...")

# 提取 cookies
cookies = ctx.cookies()
# 清理 Playwright 不支持的字段
for c in cookies:
    c.pop("sameSite", None)

# 读取现有 config.json
config_file = "config.json"
try:
    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)
except Exception:
    config = {"accounts": []}

if not config.get("accounts"):
    config["accounts"] = [{
        "username": "账号1",
        "unique_id": "",
        "cookies": [],
        "targets": [],
        "groups": [],
    }]

config["accounts"][0]["cookies"] = cookies

with open(config_file, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"cookies 已保存到 {config_file}（{len(cookies)} 个）")
print("请补充 username / unique_id / targets / groups 字段")

browser.close()
pw.stop()
