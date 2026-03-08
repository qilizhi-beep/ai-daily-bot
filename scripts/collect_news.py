#!/usr/bin/env python3
import os, re, datetime, feedparser, socket
from pathlib import Path
import google.generativeai as genai

socket.setdefaulttimeout(8)

SOURCES = [
    {"name": "量子位",   "url": "https://www.qbitai.com/feed"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    {"name": "爱范儿",   "url": "https://www.ifanr.com/feed"},
    {"name": "36氪",     "url": "https://36kr.com/feed"},
    {"name": "少数派",   "url": "https://sspai.com/feed"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat",   "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "HuggingFace",   "url": "https://huggingface.co/blog/feed.xml"},
]

def fetch_news(hours=26):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    articles = []
    for s in SOURCES:
        try:
            feed = feedparser.parse(s["url"], request_headers={"User-Agent": "Mozilla/5.0"})
            for e in feed.entries[:15]:
                pub = e.get("published_parsed") or e.get("updated_parsed")
                if pub:
                    pub_dt = datetime.datetime(*pub[:6], tzinfo=datetime.timezone.utc)
                    if pub_dt < cutoff:
                        continue
                title = e.get("title","").strip()
                if not title: continue
                summary = re.sub(r"<[^>]+>","", e.get("summary","")).strip()[:500]
                articles.append({"source": s["name"], "title": title, "summary": summary, "link": e.get("link","")})
            print(f"  ✅ {s['name']}")
        except:
            print(f"  ⚠️ {s['name']} 跳过")
    print(f"\n  📊 共 {len(articles)} 条")
    return articles

def generate_report(articles, today):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")
    news_text = "\n\n".join([
        f"[{i+1}] 来源:{a['source']}\n标题:{a['title']}\n摘要:{a['summary']}\n链接:{a['link']}"
        for i, a in enumerate(articles[:40])
    ])
    prompt = f"""你是AI领域资深编辑，将以下原始新闻整理为中文AI日报。
日期：{today}
原始新闻：
{news_text}

要求：去重筛选，每条格式：**标题** — 核心价值一句话[↗](链接)，只输出Markdown正文。

# AI 早报 {today}

## 概览

## 要闻
## 模型发布
## 开发生态
## 产品应用
## 技术与洞察
## 行业动态

---
> ⚠️ 内容由AI辅助整理，请以原文为准。"""
    response = model.generate_content(prompt)
    return response.text

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*50}\n🚀 AI日报生成 — {today}\n{'='*50}\n")
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 未设置 GEMINI_API_KEY"); exit(1)
    print("📡 抓取新闻...")
    articles = fetch_news()
    if len(articles) < 2:
        print("⚠️ 新闻太少"); exit(1)
    print("🤖 Gemini 整理中...")
    report = generate_report(articles, today)
    Path("BACKUP").mkdir(exist_ok=True)
    out = Path(f"BACKUP/{today}.md")
    out.write_text(report, encoding="utf-8")
    print(f"\n✅ 完成！已保存：{out}")
    print(report[:500])

if __name__ == "__main__":
    main()
