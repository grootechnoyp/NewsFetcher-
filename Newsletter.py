# newsletter.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import schedule
import time

def send_newsletter():
    # Fetch top news from the last 24 hours
    conn = sqlite3.connect('/Users/yashmandaviya/Newsfetcher/NewsFetcher/news.db')
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    df = pd.read_sql_query(f"SELECT title, url, topic FROM news WHERE date >= '{yesterday}' ORDER BY rating DESC LIMIT 5", conn)
    conn.close()

    # Prepare email content
    news_list = "\n".join([f"- {row['title']} ({row['topic']}): {row['url']}" for _, row in df.iterrows()])
    body = f"Daily AI News Digest - {datetime.now().strftime('%Y-%m-%d')}\n\nHere are the top 5 articles from the last 24 hours:\n{news_list}\n\nStay tuned for more updates!"

    # Read subscribers
    with open('/Users/yashmandaviya/Newsfetcher/NewsFetcher/subscribers.txt', 'r') as f:
        subscribers = [line.strip() for line in f if line.strip()]

    # Send emails
    sender = "your_email@gmail.com"  # Replace with your email
    password = "your_app_password"   # Replace with your app-specific password
    for subscriber in subscribers:
        msg = MIMEText(body)
        msg['Subject'] = f"NewsFetcher Daily Digest - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = sender
        msg['To'] = subscriber
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender, password)
                server.send_message(msg)
            print(f"Sent newsletter to {subscriber}")
        except Exception as e:
            print(f"Failed to send to {subscriber}: {e}")

# Schedule daily at 8 AM
schedule.every().day.at("08:00").do(send_newsletter)

if __name__ == "__main__":
    print("Newsletter scheduler started. Waiting for 8 AM daily...")
    while True:
        schedule.run_pending()
        time.sleep(60)