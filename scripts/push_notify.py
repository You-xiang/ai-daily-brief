# -*- coding: utf-8 -*-
"""
可选推送脚本：简报生成后把摘要推送到微信等渠道。
支持 Server酱 / PushPlus（免费微信推送服务）。
不配置 PUSH_TOKEN 时自动跳过，不影响主流程。
"""
import os
import sys
import datetime
import requests

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def main():
    token = os.environ.get("PUSH_TOKEN", "").strip()
    url = os.environ.get("PUSH_URL", "").strip()
    if not token or not url:
        print("[skip] 未配置 PUSH_TOKEN / PUSH_URL，跳过推送")
        return

    with open(os.path.join(DOCS, "brief.txt"), encoding="utf-8") as f:
        brief = f.read()

    # 推送正文截断（各平台对长度有限制），附上在线简报链接
    page_url = os.environ.get("PAGE_URL", "https://you-xiang.github.io/ai-daily-brief/")
    date_str = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime("%m-%d")
    title = f"AI行业每日简报 {date_str}"
    body = brief[:1500] + f"\n\n👉 完整简报：{page_url}"

    try:
        resp = requests.post(
            url,
            json={"title": title, "desp": body},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"[push] ok -> {resp.text[:200]}")
    except Exception as exc:
        # 推送失败不影响简报发布
        print(f"[warn] push failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
