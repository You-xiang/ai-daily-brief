# -*- coding: utf-8 -*-
"""
AI 行业每日简报生成器
流程：抓取 RSS 新闻源 -> 电信AI Store (OpenAI兼容接口) 总结 -> 生成 HTML -> 输出到 docs/index.html
"""
import json
import os
import re
import sys
import datetime
import html as html_lib

import requests
import feedparser

# ---------- 配置 ----------
BASE_URL = os.environ.get("CTYUN_BASE_URL", "https://wishub-x1.ctyun.cn/v1").rstrip("/")
API_KEY = os.environ.get("CTYUN_API_KEY", "")
MODEL = os.environ.get("CTYUN_MODEL", "deepseek-v3")

RSS_SOURCES = [
    # AI 行业新闻源（免费 RSS）
    ("机器之心", "https://www.jiqizhixin.com/rss"),
    ("量子位", "https://www.qbitai.com/feed"),
    ("36氪 AI", "https://36kr.com/feed"),
    ("Hacker News (AI", "https://hnrss.org/newest?q=AI+OR+%22large+language+model%22&count=15"),
]

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
OUT_HTML = os.path.join(DOCS_DIR, "index.html")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TeleAgent-DailyBrief/1.0"}


def fetch_news(max_per_source=8):
    """抓取所有 RSS 源，返回 [(source, title, link, summary), ...]"""
    items = []
    for name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, request_headers=UA)
            count = 0
            for e in feed.entries:
                if count >= max_per_source:
                    break
                title = html_lib.unescape(re.sub("<[^>]+>", "", e.get("title", ""))).strip()
                link = e.get("link", "")
                summary = re.sub("<[^>]+>", "", e.get("summary", e.get("description", "")))[:300].strip()
                if title:
                    items.append((name, title, link, summary))
                    count += 1
        except Exception as exc:  # 单源失败不影响整体
            print(f"[warn] fetch {name} failed: {exc}", file=sys.stderr)
    return items


def ctyun_chat(prompt, system="你是一名AI行业分析师，输出简洁、准确、信息密度高。"):
    """调用电信 AI Store（OpenAI 兼容 /chat/completions）"""
    if not API_KEY:
        raise RuntimeError("缺少 CTYUN_API_KEY，请在 GitHub 仓库 Settings -> Secrets 配置")
    url = f"{BASE_URL}/chat/completions"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def summarize(news_items):
    """让大模型把新闻列表总结成简报"""
    lines = []
    for i, (src, title, link, summ) in enumerate(news_items, 1):
        lines.append(f"{i}. [{src}] {title}\n   摘要: {summ}")
    news_text = "\n".join(lines)

    prompt = f"""以下是今天抓取的 {len(news_items)} 条 AI 行业新闻。请生成一份中文每日简报，要求：

1. 开头一段「今日焦点」：3-4 句话概括今天最重要的 AI 动向
2. 然后按「大模型与技术」「产品与应用」「行业与政策」三类归组（如某类无内容可省略）
3. 每条新闻一句话提炼（不要照抄标题），标注来源
4. 结尾一段「一线观察」：结合企业客户视角（如 ICT/云服务销售场景），给 1-2 条商机提示
5. 总字数 800 字以内，不要废话

新闻列表：
{news_text}"""
    return ctyun_chat(prompt)


def build_html(brief_text, news_items, date_str):
    """把简报文本 + 新闻列表渲染成手机友好的 HTML"""
    esc = html_lib.escape

    def fmt_brief(text):
        out = []
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                continue
            if re.match(r"^#{1,6}\s", line):
                out.append(f"<h2>{esc(line.lstrip('# '))}</h2>")
            elif re.match(r"^[-*•]\s", line):
                out.append(f"<li>{esc(line.lstrip('-*• '))}</li>")
            elif re.match(r"^\d+[.、]\s*", line):
                cleaned = re.sub(r"^\d+[.、]\s*", "", line)
                out.append("<li>" + esc(cleaned) + "</li>")
            else:
                out.append(f"<p>{esc(line)}</p>")
        return "\n".join(out)

    news_rows = "\n".join(
        f'<li><span class="src">{esc(src)}</span> <a href="{esc(link)}" target="_blank">{esc(title)}</a></li>'
        for src, title, link, _ in news_items
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 行业每日简报 {date_str}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:#f5f7fa; color:#333; line-height:1.7; }}
.wrap {{ max-width:680px; margin:0 auto; padding:16px 14px 40px; }}
.header {{ background:linear-gradient(135deg,#0066cc,#004999); color:#fff; border-radius:12px; padding:20px 18px; margin-bottom:14px; }}
.header h1 {{ font-size:20px; margin-bottom:4px; }}
.header .date {{ font-size:12px; opacity:.85; }}
.card {{ background:#fff; border-radius:12px; padding:18px 16px; margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,.06); }}
.card h2 {{ font-size:15px; color:#0066cc; margin:14px 0 6px; border-left:3px solid #0066cc; padding-left:8px; }}
.card h2:first-child {{ margin-top:0; }}
.card p {{ font-size:14px; margin:6px 0; }}
.card li {{ font-size:14px; margin:4px 0 4px 18px; }}
.news h2 {{ border-left-color:#e67e22; color:#d35400; }}
.news ol {{ margin-left:6px; }}
.news a {{ color:#0066cc; text-decoration:none; font-size:14px; }}
.news .src {{ display:inline-block; background:#eef4ff; color:#0066cc; font-size:11px; border-radius:4px; padding:1px 6px; margin-right:4px; }}
.footer {{ text-align:center; font-size:11px; color:#aaa; margin-top:20px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>AI 行业每日简报</h1>
    <div class="date">{date_str} · 由电信 AI Store 大模型自动生成</div>
  </div>
  <div class="card">{fmt_brief(brief_text)}</div>
  <div class="card news">
    <h2>今日新闻源</h2>
    <ol>
{news_rows}
    </ol>
  </div>
  <div class="footer">GitHub Actions 每日 09:00 自动生成 · 内容仅供参考</div>
</div>
</body>
</html>"""


def main():
    date_str = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).strftime("%Y-%m-%d %A")

    print("[1/3] 抓取新闻源...")
    news = fetch_news()
    if not news:
        print("[error] 所有新闻源均抓取失败", file=sys.stderr)
        sys.exit(1)
    print(f"      共 {len(news)} 条")

    print("[2/3] 调用电信 AI Store 生成简报...")
    brief = summarize(news)

    print("[3/3] 渲染 HTML...")
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(build_html(brief, news, date_str))
    # 保存纯文本副本，供推送脚本使用
    with open(os.path.join(DOCS_DIR, "brief.txt"), "w", encoding="utf-8") as f:
        f.write(brief)
    print(f"done -> {OUT_HTML}")


if __name__ == "__main__":
    main()
