# app.py (optimized for Railway)
import streamlit as st
import sqlite3
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Page config
st.set_page_config(page_title="NewsFetcher", layout="wide")

# Minimal CSS (reduce overhead)
st.markdown("""
    <style>
    body { background: #1e1e3b; color: #ffffff; font-family: sans-serif; }
    .header { font-size: 36px; color: #00e5ff; text-align: center; }
    .news-card { background: rgba(255, 255, 255, 0.1); padding: 15px; margin: 10px 0; border-radius: 8px; }
    .news-title { font-size: 18px; color: #00e5ff; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {'topics': [], 'language': 'en'}
if 'current_news' not in st.session_state:
    st.session_state.current_news = ""

# AI Tools (on-demand loading)
def get_summarizer():
    if 'summarizer' not in st.session_state:
        st.session_state.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    return st.session_state.summarizer

def get_chatbot():
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = pipeline("text2text-generation", model="facebook/blenderbot_small-90M")
    return st.session_state.chatbot

analyzer = SentimentIntensityAnalyzer()  # Lightweight, load at startup

# Database Setup
def get_db_connection():
    conn = sqlite3.connect('news.db', timeout=10)
    return conn

@st.cache_data
def fetch_news_data(page=1, personalized=False, user_prefs=None):
    with get_db_connection() as conn:
        query = "SELECT id, title, url, date, topic, source, language FROM news WHERE 1=1"
        if personalized and user_prefs and user_prefs.get('topics'):
            query += f" AND topic IN ({','.join([f"'{t}'" for t in user_prefs['topics']])})"
        query += f" ORDER BY date DESC LIMIT 10 OFFSET {(page - 1) * 10}"
        df = pd.read_sql_query(query, conn)
        total_items = pd.read_sql_query("SELECT COUNT(*) FROM news", conn).iloc[0, 0]
    return df, total_items

# Main UI
st.markdown('<div class="header">NewsFetcher: AI Boom</div>', unsafe_allow_html=True)

# Crypto Prices
@st.cache_data(ttl=300)
def fetch_crypto_prices():
    return requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd").json()

crypto_prices = fetch_crypto_prices()
if 'bitcoin' in crypto_prices:
    st.write(f"BTC: ${crypto_prices['bitcoin']['usd']} | ETH: ${crypto_prices['ethereum']['usd']}")

# News Feed
st.subheader("AI News Feed")
page = st.number_input("Page", min_value=1, value=1)
personalized = st.checkbox("Personalized Feed")
news_df, total_items = fetch_news_data(page, personalized, st.session_state.user_prefs)

if not news_df.empty:
    st.session_state.current_news = "\n".join(news_df['title'].tolist())
    for i, row in news_df.iterrows():
        sentiment = analyzer.polarity_scores(row['title'])['compound']
        sentiment_label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
        summary = get_summarizer()(row['title'], max_length=15, min_length=5, do_sample=False)[0]['summary_text']
        st.markdown(f"""
            <div class="news-card">
                <div class="news-title">{row['title']}</div>
                <p>Source: {row['source']} | Topic: {row['topic']} | Sentiment: {sentiment_label}</p>
                <p>Summary: {summary}</p>
                <a href="{row['url']}" target="_blank">Read More</a>
            </div>
        """, unsafe_allow_html=True)
    st.write(f"Showing {len(news_df)} of {total_items} articles")

# Chatbot (load only when used)
if st.button("Open Chatbot"):
    st.session_state.chat_open = True
if 'chat_open' in st.session_state and st.session_state.chat_open:
    message = st.text_input("Ask the AI:")
    if message:
        chatbot = get_chatbot()
        response = chatbot(f"News: {st.session_state.current_news[:500]}\nUser: {message}", max_length=100)[0]['generated_text']
        st.write(f"AI: {response}")

# Run on Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8501))
    st._is_running_with_streamlit = True
    import streamlit.web.bootstrap as bootstrap
    bootstrap.run("app.py", "", [], {"server.port": port, "server.headless": True})
