import feedparser
import requests
import datetime
import os
import re
import time

# Telegram 設定
# ✅ 正確的寫法
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHANNEL_ID = os.getenv("TG_CHANNEL_ID")


# 資安 RSS 源
RSS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://krebsonsecurity.com/feed/"
]

def generate_tags(title, summary):
    """關鍵字匹配生成標籤"""
    text = (title + " " + summary).lower()
    tags = []
    
    rules = {
        "ransomware|勒索": "#勒索軟體",
        "cve|漏洞|vulnerability": "#漏洞",
        "phishing|釣魚": "#釣魚攻擊",
        "zero-day|0day|零時差": "#零時差",
        "data breach|外洩|leak": "#資料外洩",
        "malware|malicious|惡意": "#惡意軟體"
    }
    
    for keywords, tag in rules.items():
        if re.search(keywords, text):
            tags.append(tag)
            
    if not tags:
        tags.append("#資安情報")
        
    return " ".join(tags)

def fetch_latest_news():
    """抓取過去 24 小時的新聞"""
    news_list = []
    yesterday = datetime.datetime.now() - datetime.timedelta(hours=24)
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime.datetime(*entry.published_parsed[:6])
                    if published_time < yesterday:
                        continue
                
                raw_summary = entry.get("summary", entry.get("description", ""))
                clean_summary = re.sub('<[^<]+>', '', raw_summary).strip()
                short_summary = clean_summary[:200] + "..." if len(clean_summary) > 200 else clean_summary

                news_list.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": short_summary
                })
        except Exception as e:
            print(f"抓取 {feed_url} 失敗: {e}")
            
    return news_list

def format_message(news_item):
    """格式化訊息"""
    tags = generate_tags(news_item['title'], news_item['summary'])
    
    message = f"""
 <b>{news_item['title']}</b>

📝 {news_item['summary']}

 <a href="{news_item['link']}">閱讀原文</a>

🏷️ {tags}
    """
    return message.strip()

def send_to_telegram(message):
    """發送到 Telegram"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"發送失敗: {response.text}")
    else:
        print("發送成功！")

def main():
    print("開始抓取最新資安新聞...")
    news = fetch_latest_news()
    
    if not news:
        print("今天沒有新的資安新聞。")
        return
        
    print(f"共找到 {len(news)} 則新聞，準備發送...")
    
    # 限制最多發送 15 則，避免洗版
    if len(news) > 15:
        news = news[:15]
        print(f"新聞過多，只發送前 15 則")
    
    for item in news:
        msg = format_message(item)
        send_to_telegram(msg)
        time.sleep(2)  # 避免觸發 API 限制
    
    print("全部發送完成！")

if __name__ == "__main__":
    main()
