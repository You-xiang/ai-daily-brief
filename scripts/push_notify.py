# -*- coding: utf-8 -*-
"""
每日简报微信推送脚本。
支持 Server酱（推荐，免费、微信直接接收）与 PushPlus。
不配置 SENDKEY 时自动跳过，不影响简报生成发布主流程。
"""
import os
import sys
import datetime
import requests

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def push_serverchan(sendkey, title, body):
    """Server酱：https://sct.ftqq.com/ 扫码获取 SENDKEY"""
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    resp = requests.post(url, data={"title": title, "desp": body}, timeout=30)
    resp.raise_for_status()
    return resp.text


def push_pushplus(token, title, body):
    """PushPlus：http://www.pushplus.plus/ 扫码获取 token"""
    url = "http://www.pushplus.plus/send"
    resp = requests.post(
        url,
        json={"token": token, "title": title, "content": body, "template": "markdown"},
        headers={"Content-Type": "application/json"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def main():
    brief_path = os.path.join(DOCS, "brief.txt")
    if not os.path.exists(brief_path):
        print("[skip] 未找到 brief.txt，跳过推送")
        return

    with open(brief_path, encoding="utf-8") as f:
        brief = f.read()

    page_url = os.environ.get("PAGE_URL", "https://you-xiang.github.io/ai-daily-brief/")
    date_str = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime("%m-%d")
    title = f"AI行业每日简报 {date_str}"
    # Server酱 desp 支持 Markdown，正文截断到 1500 字内，附在线简报链接
    body = brief[:1500] + f"\n\n---\n\n👉 完整简报：{page_url}"

    # Server酱优先
    sendkey = os.environ.get("SC_KEY", "").strip()
    if sendkey:
        try:
            r = push_serverchan(sendkey, title, body)
            print(f"[push] Server酱 ok -> {r.text[:200]}")
        except Exception as exc:
            print(f"[warn] Server酱 push failed: {exc}", file=sys.stderr)
        return

    # PushPlus 备用
    token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if token:
        try:
            r = push_pushplus(token, title, body)
            print(f"[push] PushPlus ok -> {r[:200]}")
        except Exception as exc:
            print(f"[warn] PushPlus push failed: {exc}", file=sys.stderr)
        return

    print("[skip] 未配置 SENDKEY / PUSHPLUS_TOKEN，跳过推送")


if __name__ == "__main__":
    main()