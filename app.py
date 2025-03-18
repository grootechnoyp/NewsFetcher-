# app.py
import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np
import plotly.express as px
from gtts import gTTS
from io import BytesIO
import base64
import smtplib
from email.mime.text import MIMEText
import json
import queue
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["MKL_THREADING_LAYER"] = "GNU"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Page config
st.set_page_config(page_title="NewsFetcher", layout="wide", initial_sidebar_state="collapsed")

# AI Boom CSS (unchanged)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    body {
        background: linear-gradient(135deg, #1e1e3b 0%, #4b0082 100%);
        font-family: 'Poppins', sans-serif;
        color: #ffffff;
        overflow-x: hidden;
    }
    .main-container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    .header { font-size: 48px; font-weight: 600; color: #00e5ff; text-align: center; margin-bottom: 30px; animation: fadeIn 1s ease-in; }
    .crypto-bar { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; display: flex; justify-content: center; gap: 30px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.1); }
    .crypto-item { display: flex; align-items: center; gap: 10px; font-size: 20px; color: #e0e0ff; }
    .search-bar { background: rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0, 229, 255, 0.05); }
    .news-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
    .news-card { background: rgba(255, 255, 255, 0.03); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.1); transition: all 0.3s ease; }
    .news-card:hover { transform: translateY(-5px); box-shadow: 0 6px 20px rgba(0, 229, 255, 0.2); }
    .news-title { font-size: 18px; font-weight: 600; color: #00e5ff; margin-bottom: 10px; }
    .news-meta { font-size: 14px; color: #b0b0ff; margin-bottom: 5px; }
    .feature-panel { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; margin-top: 30px; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.1); }
    .feature-button { background: linear-gradient(45deg, #00e5ff, #4b0082); color: #ffffff; padding: 10px 20px; border-radius: 8px; margin: 5px; cursor: pointer; transition: all 0.3s ease; }
    .feature-button:hover { background: linear-gradient(45deg, #4b0082, #00e5ff); box-shadow: 0 2px 10px rgba(0, 229, 255, 0.3); }
    .sidebar-panel { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.1); }
    .chat-ai { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
    .chat-button { background: linear-gradient(45deg, #00e5ff, #4b0082); border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3); cursor: pointer; transition: all 0.3s ease; }
    .chat-button:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(0, 229, 255, 0.5); }
    .chat-window { position: absolute; bottom: 80px; right: 0; width: 320px; height: 400px; background: rgba(30, 30, 59, 0.95); border-radius: 12px; padding: 15px; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.2); display: none; animation: slideUp 0.3s ease-out; }
    .chat-window.active { display: block; }
    .chat-header { font-size: 18px; font-weight: 600; color: #00e5ff; margin-bottom: 10px; }
    .chat-history { height: 300px; overflow-y: auto; color: #e0e0ff; font-size: 14px; }
    .chat-input { width: 100%; background: rgba(255, 255, 255, 0.1); border: none; padding: 10px; border-radius: 8px; color: #ffffff; margin-top: 10px; outline: none; }
    @keyframes fadeIn { 0% {opacity: 0;} 100% {opacity: 1;} }
    @keyframes slideUp { 0% {opacity: 0; transform: translateY(20px);} 100% {opacity: 1; transform: translateY(0);} }
    </style>
""", unsafe_allow_html=True)

# Icons (unchanged)
BTC_ICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIj48cGF0aCBmaWxsPSIjZmZhNTAwIiBkPSJNMjU2IDBDMTE0LjYgMCAwIDExNC42IDAgMjU2czExNC42IDI1NiAyNTYgMjU2IDI1Ni0xMTQuNiAyNTYtMjU2UzM5Ny40IDAgMjU2IDBaTTM2OC42IDE0NC42Yy03LjEtMTQuNS0yMS41LTI0LjQtMzguNi0yNC42di01Ni43aC0zMi41djU0LjFjLTguNSAwLTE3LjEtLjEtMjUuNi4ydjU1LjFjOC41LS4zIDE3LjEuMiAyNS42LjJ2NTQuOWgtMjUuNmMtMjMuNiAwLTQyLjcgMTkuMi00Mi43IDQyLjdzMTkuMiA0Mi43IDQyLjcgNDIuN2gyNS42djEwOC41aDMzLjR2MTA2LjZjMTcuMi0uMiAzMS42LTEwLjEgMzguNy0yNC42IDExLjQtMjMuNSAxMC40LTUxLjQtMi41LTczLjgtMTIuOS0yMi40LTM3LjUtMzYuNS02Mi44LTM2LjVoLTI1LjZjLTEwLjkgMC0xOS43LTguOC0xOS43LTE5LjcgMC0xMC45IDguOC0xOS43IDE5LjctMTkuN2gyNS42YzI1LjMgMCA0OS45LTE0LjEgNjIuOC0zNi41IDEyLjktMjIuNCAxMy45LTUwLjMgMi41LTczLjhaIi8+PC9zdmc+"
ETH_ICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIj48cGF0aCBmaWxsPSIjNjI3ZWVhIiBkPSJNMjU2IDBDMTE0LjYgMCAwIDExNC42IDAgMjU2czExNC42IDI1NiAyNTYgMjU2IDI1Ni0xMTQuNiAyNTYtMjU2UzM5Ny40IDAgMjU2IDBaTTI1NS45IDE2NC43di5sMTExLjkgMTY0LjgtMTExLjktMTMuNXYxMzUuM2gtLjF2LTEzNS5zbC0xMTEuOSAxMy41TDI1NS45IDE2NC43WiIvPjwvc3ZnPg=="
CHAT_ICON = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjU2IDBDMTE0LjYgMCAwIDExNC42IDAgMjU2czExNC42IDI1NiAyNTYgMjU2IDI1Ni0xMTQuNiAyNTYtMjU2UzM5Ny40IDAgMjU2IDBaTTM4NCAxNjBjMCA4OC40LTcxLjYgMTYwLTE2MCAxNjBzLTE2MC03MS42LTE2MC0xNjBjMC03Ny41IDU1LjEtMTQyLjMgMTI4LjctMTU1LjJjLTkuMSAyLjMtMTcuNyA2LjQtMjQuNiAxMi4xLTI3LjUgMjIuMy00NS4zIDU2LjgtNDUuMyA5NC45IDAgNjQuNCA1Mi4xIDExNi41IDExNi41IDExNi41czExNi41LTUyLjEgMTE2LjUtMTE2LjVjMC0zOC4xLTE3LjgtNzIuNi00NS4zLTk0LjktNi45LTUuNy0xNS41LTkuOC0yNC42LTEyLjFDMzI4LjkgMTguMyAzODQgODMuMSAzODQgMTYwWiIvPjwvc3ZnPg=="

# Initialize session state (unchanged)
if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {'topics': [], 'language': 'en', 'email': '', 'dashboard': ['news', 'timeline', 'insights']}
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = "All"
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "All"
if 'sort_by' not in st.session_state:
    st.session_state.sort_by = "Date (Newest)"
if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_news' not in st.session_state:
    st.session_state.current_news = ""
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0
if 'quiz_taken' not in st.session_state:
    st.session_state.quiz_taken = False
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = []
if 'comment_queues' not in st.session_state:
    st.session_state.comment_queues = {}
if 'hot_takes' not in st.session_state:
    st.session_state.hot_takes = {}

# AI Tools (optimized with lighter models)
@st.cache_resource
def load_models():
    return {
        'analyzer': SentimentIntensityAnalyzer(),
        'summarizer': pipeline("summarization", model="sshleifer/distilbart-cnn-12-6"),  # Lighter model
        'chatbot': pipeline("text2text-generation", model="facebook/blenderbot_small-90M"),  # Much smaller
        'translator': pipeline("translation", model="Helsinki-NLP/opus-mt-en-es"),
        'embedder': SentenceTransformer('all-MiniLM-L6-v2'),  # Lightweight
        'hot_take_generator': pipeline("text-generation", model="distilgpt2", device=-1)  # CPU-only
    }

models = load_models()
analyzer = models['analyzer']
summarizer = models['summarizer']
chatbot = models['chatbot']
translator = models['translator']
embedder = models['embedder']
hot_take_generator = models['hot_take_generator']

# Database Setup
def get_db_connection():
    conn = sqlite3.connect('news.db', timeout=10)  # Relative path for Streamlit Cloud
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS subscribers (email TEXT UNIQUE, join_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS quiz_scores (username TEXT, score INTEGER, date TEXT)")
        conn.commit()

init_db()

# Database Functions (unchanged)
@st.cache_data
def fetch_news_data(page=1, personalized=False, user_prefs=None):
    with get_db_connection() as conn:
        query = "SELECT id, title, url, date, topic, source, language, rating FROM news WHERE 1=1"
        if st.session_state.selected_topic != "All":
            query += f" AND topic = '{st.session_state.selected_topic}'"
        if st.session_state.selected_language != "All":
            query += f" AND language = '{st.session_state.selected_language}'"
        if st.session_state.search_query:
            query += f" AND (title LIKE '%{st.session_state.search_query}%' OR topic LIKE '%{st.session_state.search_query}%')"
        if personalized and user_prefs:
            topics = user_prefs.get('topics', [])
            if topics:
                query += f" AND topic IN ({','.join([f"'{t}'" for t in topics])})"
        if st.session_state.sort_by == "Date (Newest)":
            query += " ORDER BY date DESC"
        elif st.session_state.sort_by == "Date (Oldest)":
            query += " ORDER BY date ASC"
        elif st.session_state.sort_by == "Source":
            query += " ORDER BY source, date DESC"
        else:
            query += " ORDER BY rating DESC, date DESC"
        offset = (page - 1) * 10
        query += f" LIMIT 10 OFFSET {offset}"
        df = pd.read_sql_query(query, conn)
        total_items = pd.read_sql_query("SELECT COUNT(*) FROM news WHERE 1=1" + 
                                        (f" AND topic = '{st.session_state.selected_topic}'" if st.session_state.selected_topic != "All" else "") + 
                                        (f" AND language = '{st.session_state.selected_language}'" if st.session_state.selected_language != "All" else "") + 
                                        (f" AND (title LIKE '%{st.session_state.search_query}%' OR topic LIKE '%{st.session_state.search_query}%')" if st.session_state.search_query else "") +
                                        (f" AND topic IN ({','.join([f"'{t}'" for t in user_prefs['topics']])})" if personalized and user_prefs and user_prefs.get('topics') else ""), conn).iloc[0, 0]
    return df, total_items

def update_rating(news_id, rating):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE news SET rating = ? WHERE id = ?", (rating, news_id))
        conn.commit()

def add_subscriber(email):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO subscribers (email, join_date) VALUES (?, ?)", (email, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

def save_quiz_score(username, score):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quiz_scores (username, score, date) VALUES (?, ?, ?)", (username, score, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        leaderboard_df = pd.read_sql_query("SELECT username, MAX(score) as score FROM quiz_scores GROUP BY username ORDER BY score DESC LIMIT 5", conn)
        st.session_state.leaderboard = leaderboard_df.to_dict('records')

# Gamification, Audio, Email, Crypto, Clustering, Cache, Comments, Hot Takes, Quiz (unchanged)
def update_points(action, points):
    if 'points' not in st.session_state:
        st.session_state.points = 0
    st.session_state.points += points
    st.session_state[f"{action}_count"] = st.session_state.get(f"{action}_count", 0) + 1

def text_to_audio(text):
    tts = gTTS(text=text, lang='en', slow=False)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return audio_file

def send_email_alert(subject, body, to_email):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    if not sender or not password:
        st.error("Email credentials not set in environment variables.")
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        st.success("Email sent!")
    except Exception as e:
        st.error(f"Email failed: {e}")

@st.cache_data(ttl=300)
def fetch_crypto_prices():
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
    return response.json()

@st.cache_data
def cluster_news(df):
    if len(df) < 2:
        df['cluster'] = 0
        return df
    embeddings = embedder.encode(df['title'].tolist())
    kmeans = KMeans(n_clusters=min(5, len(df)), random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    df['cluster'] = clusters
    return df

def save_offline_cache(news_df):
    with open("offline_cache.json", "w") as f:
        json.dump(news_df.to_dict('records'), f)

def load_offline_cache():
    try:
        with open("offline_cache.json", "r") as f:
            return pd.DataFrame(json.load(f))
    except:
        return None

def handle_comments(news_id, comment):
    if news_id not in st.session_state.comment_queues:
        st.session_state.comment_queues[news_id] = queue.Queue()
    st.session_state.comment_queues[news_id].put(f"{datetime.now()} | {st.session_state.get('username', 'Anonymous')}: {comment}")

def generate_hot_take(title):
    prompt = f"Give a bold, witty hot take on this news: {title}"
    take = hot_take_generator(prompt, max_length=50, num_return_sequences=1, do_sample=True, temperature=0.9)[0]['generated_text']
    return take.strip()

def generate_quiz():
    with get_db_connection() as conn:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        df = pd.read_sql_query(f"SELECT title, topic, source FROM news WHERE date >= '{yesterday}' ORDER BY rating DESC LIMIT 10", conn)
    if len(df) < 3:
        return None
    questions = []
    for _ in range(3):
        article = df.sample(1).iloc[0]
        question = f"What is the topic of the article '{article['title']}'?"
        correct_answer = article['topic']
        wrong_answers = df['topic'].drop_duplicates().tolist()
        wrong_answers.remove(correct_answer)
        options = [correct_answer] + random.sample(wrong_answers, min(3, len(wrong_answers)))
        random.shuffle(options)
        questions.append({"question": question, "options": options, "correct": correct_answer})
    return questions

def display_quiz():
    st.subheader("Daily AI News Quiz")
    username = st.text_input("Enter your username", value=st.session_state.get('username', 'Anonymous'))
    st.session_state.username = username
    quiz = generate_quiz()
    if not quiz:
        st.write("Not enough news today—check back tomorrow!")
        return
    if not st.session_state.quiz_taken:
        answers = []
        for i, q in enumerate(quiz):
            st.write(f"Q{i+1}: {q['question']}")
            answer = st.radio(f"Options_{i}", q['options'], key=f"quiz_{i}")
            answers.append(answer)
        if st.button("Submit Quiz"):
            score = sum(10 for i, ans in enumerate(answers) if ans == quiz[i]['correct'])
            st.session_state.quiz_score = score
            st.session_state.quiz_taken = True
            save_quiz_score(username, score)
            st.success(f"Your score: {score}/30")
    else:
        st.write(f"Your score today: {st.session_state.quiz_score}/30")
    if st.button("Reset Quiz", key="reset_quiz"):
        st.session_state.quiz_taken = False
        st.session_state.quiz_score = 0
        st.rerun()

# Main UI (optimized)
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.markdown('<div class="header">NewsFetcher: AI Boom</div>', unsafe_allow_html=True)

# Crypto Bar
crypto_prices = fetch_crypto_prices()
if 'bitcoin' in crypto_prices:
    st.markdown(f"""
        <div class="crypto-bar">
            <div class="crypto-item"><img src="{BTC_ICON}" width="30" height="30"> BTC: ${crypto_prices['bitcoin']['usd']}</div>
            <div class="crypto-item"><img src="{ETH_ICON}" width="30" height="30"> ETH: ${crypto_prices['ethereum']['usd']}</div>
        </div>
    """, unsafe_allow_html=True)

# Search and Toggles
st.markdown('<div class="search-bar">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.session_state.search_query = st.text_input("Search AI News", placeholder="Enter keywords...", key="search")
with col2:
    real_time = st.checkbox("Real-Time AI", value=False)
with col3:
    personalized = st.checkbox("Personalized Feed", value=False)
st.markdown('</div>', unsafe_allow_html=True)

# News Grid with Hot Takes
st.subheader("AI News Feed")
page = st.number_input("Page", min_value=1, value=1, step=1)
if real_time:
    placeholder = st.empty()
    while real_time:
        with st.spinner("Fetching real-time AI news..."):
            with placeholder.container():
                news_df, total_items = fetch_news_data(page, personalized, st.session_state.user_prefs)
                news_df = cluster_news(news_df)
                if not news_df.empty:
                    save_offline_cache(news_df)
                    st.session_state.current_news = "\n".join(news_df['title'].tolist())
                    st.markdown('<div class="news-grid">', unsafe_allow_html=True)
                    for i, row in news_df.iterrows():
                        sentiment = analyzer.polarity_scores(row['title'])['compound']
                        sentiment_label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
                        summary = summarizer(row['title'], max_length=15, min_length=5, do_sample=False)[0]['summary_text']
                        translated_summary = translator(summary)[0]['translation_text'] if st.session_state.user_prefs.get('language', 'en') != 'en' else summary
                        topic_color = {"artificial intelligence": "#00e5ff", "blockchain": "#ff4081", "cryptocurrency": "#ffeb3b", "cybersecurity": "#ff5722"}.get(row['topic'], "#ffffff")
                        st.markdown(f"""
                            <div class="news-card">
                                <div class="news-title" style="color: {topic_color}">{row['title']}</div>
                                <div class="news-meta">Source: {row['source']} | Topic: {row['topic']} | Sentiment: {sentiment_label} | Cluster: {row['cluster']}</div>
                                <div class="news-meta">Summary: {translated_summary}</div>
                                <div class="news-meta">Rating: {row['rating']:.1f} | Published: {row['date']}</div>
                                <a href="{row['url']}" target="_blank" style="color: #00e5ff;">Read More</a>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Listen", key=f"audio_{row['id']}"):
                            audio = text_to_audio(translated_summary)
                            st.audio(audio, format='audio/mp3')
                        tweet_url = f"https://twitter.com/intent/tweet?text={row['title'][:100]}%20{row['url']}%20via%20NewsFetcher"
                        linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={row['url']}"
                        st.markdown(f"<a href='{tweet_url}' style='color: #00e5ff;'>Tweet</a> | <a href='{linkedin_url}' style='color: #00e5ff;'>Share</a>", unsafe_allow_html=True)
                        new_rating = st.slider("Rate", 0.0, 5.0, float(row['rating']), step=0.5, key=f"rating_{row['id']}")
                        if new_rating != row['rating']:
                            update_rating(row['id'], new_rating)
                            update_points("rating", 5)
                            st.rerun()
                        comment = st.text_input(f"Comment on {row['title']}", key=f"comment_{row['id']}")
                        if st.button("Post", key=f"post_{row['id']}"):
                            handle_comments(row['id'], comment)
                            update_points("comment", 10)
                        if row['id'] in st.session_state.comment_queues and not st.session_state.comment_queues[row['id']].empty():
                            st.write("Comments:")
                            while not st.session_state.comment_queues[row['id']].empty():
                                st.markdown(f'<div class="news-meta">{st.session_state.comment_queues[row["id"]].get()}</div>', unsafe_allow_html=True)
                        if st.button("Hot Take", key=f"hot_take_{row['id']}"):
                            hot_take = generate_hot_take(row['title'])
                            st.session_state.hot_takes[row['id']] = hot_take
                            update_points("hot_take", 5)
                        if row['id'] in st.session_state.hot_takes:
                            st.markdown(f'<div class="news-meta">Hot Take: {st.session_state.hot_takes[row["id"]]}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.write(f"Showing {len(news_df)} of {total_items} articles")
                time.sleep(60)
else:
    news_df, total_items = fetch_news_data(page, personalized, st.session_state.user_prefs)
    news_df = cluster_news(news_df)
    if not news_df.empty:
        save_offline_cache(news_df)
        st.session_state.current_news = "\n".join(news_df['title'].tolist())
        st.markdown('<div class="news-grid">', unsafe_allow_html=True)
        for i, row in news_df.iterrows():
            sentiment = analyzer.polarity_scores(row['title'])['compound']
            sentiment_label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
            summary = summarizer(row['title'], max_length=15, min_length=5, do_sample=False)[0]['summary_text']
            translated_summary = translator(summary)[0]['translation_text'] if st.session_state.user_prefs.get('language', 'en') != 'en' else summary
            topic_color = {"artificial intelligence": "#00e5ff", "blockchain": "#ff4081", "cryptocurrency": "#ffeb3b", "cybersecurity": "#ff5722"}.get(row['topic'], "#ffffff")
            st.markdown(f"""
                <div class="news-card">
                    <div class="news-title" style="color: {topic_color}">{row['title']}</div>
                    <div class="news-meta">Source: {row['source']} | Topic: {row['topic']} | Sentiment: {sentiment_label} | Cluster: {row['cluster']}</div>
                    <div class="news-meta">Summary: {translated_summary}</div>
                    <div class="news-meta">Rating: {row['rating']:.1f} | Published: {row['date']}</div>
                    <a href="{row['url']}" target="_blank" style="color: #00e5ff;">Read More</a>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Listen", key=f"audio_{row['id']}"):
                audio = text_to_audio(translated_summary)
                st.audio(audio, format='audio/mp3')
            tweet_url = f"https://twitter.com/intent/tweet?text={row['title'][:100]}%20{row['url']}%20via%20NewsFetcher"
            linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={row['url']}"
            st.markdown(f"<a href='{tweet_url}' style='color: #00e5ff;'>Tweet</a> | <a href='{linkedin_url}' style='color: #00e5ff;'>Share</a>", unsafe_allow_html=True)
            new_rating = st.slider("Rate", 0.0, 5.0, float(row['rating']), step=0.5, key=f"rating_{row['id']}")
            if new_rating != row['rating']:
                update_rating(row['id'], new_rating)
                update_points("rating", 5)
                st.rerun()
            comment = st.text_input(f"Comment on {row['title']}", key=f"comment_{row['id']}")
            if st.button("Post", key=f"post_{row['id']}"):
                handle_comments(row['id'], comment)
                update_points("comment", 10)
            if row['id'] in st.session_state.comment_queues and not st.session_state.comment_queues[row['id']].empty():
                st.write("Comments:")
                while not st.session_state.comment_queues[row['id']].empty():
                    st.markdown(f'<div class="news-meta">{st.session_state.comment_queues[row["id"]].get()}</div>', unsafe_allow_html=True)
            if st.button("Hot Take", key=f"hot_take_{row['id']}"):
                hot_take = generate_hot_take(row['title'])
                st.session_state.hot_takes[row['id']] = hot_take
                update_points("hot_take", 5)
            if row['id'] in st.session_state.hot_takes:
                st.markdown(f'<div class="news-meta">Hot Take: {st.session_state.hot_takes[row["id"]]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.write(f"Showing {len(news_df)} of {total_items} articles")
    else:
        offline_df = load_offline_cache()
        if offline_df is not None:
            st.write("Offline Mode: Cached Articles")
            st.dataframe(offline_df)
        else:
            st.write("No articles found.")

# Feature Panel (unchanged)
st.markdown('<div class="feature-panel">', unsafe_allow_html=True)
st.subheader("AI Features")
feature_cols = st.columns(3)
menu_options = {
    "Timeline": lambda: st.plotly_chart(px.line(pd.read_sql_query("SELECT date, topic, COUNT(*) as count FROM news GROUP BY date, topic", get_db_connection()), x="date", y="count", color="topic", title="News Timeline")),
    "Insights": lambda: (st.write("AI Insights:"), st.dataframe(pd.read_sql_query("SELECT topic, AVG(rating) as avg_rating, COUNT(*) as count FROM news GROUP BY topic", get_db_connection()))),
    "Stats": lambda: st.bar_chart(pd.read_sql_query("SELECT source, COUNT(*) as count FROM news GROUP BY source", get_db_connection()).set_index('source')),
    "Recommendations": lambda: st.dataframe(pd.read_sql_query("SELECT title, topic, rating FROM news WHERE rating > 0 ORDER BY rating DESC LIMIT 5", get_db_connection())),
    "Submit News": lambda: (user_title := st.text_input("Article Title"), user_url := st.text_input("Article URL"), st.button("Submit") and (conn := get_db_connection(), conn.execute("INSERT INTO news (title, url, date, topic, source, language, rating) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_title, user_url, datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"), "user-submitted", "Community", "en", 0.0)), conn.commit(), conn.close(), st.success("Article submitted!"))),
    "Keyword Alerts": lambda: (alert_keyword := st.text_input("Set Alert Keyword"), st.button("Set Alert") and (st.session_state.__setitem__('alert_keyword', alert_keyword), st.success(f"Alert set for '{alert_keyword}'!"))),
    "Export & Share": lambda: (col1, col2 := st.columns(2), col1.download_button("Export CSV", pd.read_sql_query("SELECT * FROM news", get_db_connection()).to_csv(index=False), "news.csv", "text/csv"), col2.markdown("<a href='https://twitter.com/intent/tweet?text=Check%20out%20NewsFetcher!%20https://newsfetcher.streamlit.app' target='_blank' style='color: #00e5ff;'>Tweet</a>", unsafe_allow_html=True)),
    "Newsletter Signup": lambda: (email := st.text_input("Enter your email for daily news"), st.button("Subscribe") and (add_subscriber(email), st.success("Subscribed! You’ll receive daily AI news updates."))),
    "Daily Quiz": lambda: display_quiz()
}
for i, (name, func) in enumerate(menu_options.items()):
    with feature_cols[i % 3]:
        if st.button(name, key=f"feature_{name}"):
            func()
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar Panel (unchanged)
with st.sidebar:
    st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
    st.title("AI Controls")
    st.session_state.selected_topic = st.selectbox("Filter Topic", ["All", "artificial intelligence", "blockchain", "cryptocurrency", "cybersecurity"])
    st.session_state.selected_language = st.selectbox("Language", ["All", "en", "es", "fr", "de"])
    st.session_state.sort_by = st.selectbox("Sort By", ["Date (Newest)", "Date (Oldest)", "Source", "Rating"])
    pref_topics = st.multiselect("Preferred Topics", ["artificial intelligence", "blockchain", "cryptocurrency", "cybersecurity"], default=st.session_state.user_prefs['topics'])
    pref_language = st.selectbox("Preferred Language", ["en", "es", "fr", "de"], index=["en", "es", "fr", "de"].index(st.session_state.user_prefs['language']))
    pref_email = st.text_input("Email for Alerts", value=st.session_state.user_prefs['email'])
    if st.button("Save Preferences"):
        st.session_state.user_prefs = {'topics': pref_topics, 'language': pref_language, 'email': pref_email, 'dashboard': st.session_state.user_prefs['dashboard']}
        st.success("Preferences saved!")
    st.write(f"Points: {st.session_state.get('points', 0)}")
    st.subheader("Quiz Leaderboard")
    if st.session_state.leaderboard:
        for entry in st.session_state.leaderboard:
            st.write(f"{entry['username']}: {entry['score']}")
    else:
        st.write("No scores yet—take the quiz!")
    st.markdown('</div>', unsafe_allow_html=True)

# Chatbot UI (simplified)
st.markdown(f"""
    <div class="chat-ai">
        <div class="chat-button" id="chat-toggle">
            <img src="{CHAT_ICON}" width="30" height="30" alt="Chat Icon">
        </div>
        <div id="chat-window" class="chat-window{' active' if st.session_state.chat_open else ''}">
            <div class="chat-header">AI Assistant</div>
            <div class="chat-history" id="chat-history">
                {"".join([f'<p>{msg}</p>' for msg in st.session_state.chat_history])}
            </div>
            <input id="chat-input" class="chat-input" placeholder="Ask me anything..." onkeypress="if(event.key === 'Enter') {{sendChat();}}">
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <script>
    let chatOpen = false;
    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');

    chatToggle.addEventListener('click', () => {
        chatOpen = !chatOpen;
        chatWindow.classList.toggle('active', chatOpen);
        window.parent.postMessage({'chat_open': chatOpen}, '*');
        if (chatOpen) chatInput.focus();
    });

    function sendChat() {
        const message = chatInput.value.trim();
        if (message) {
            const userMsg = document.createElement('p');
            userMsg.textContent = 'You: ' + message;
            chatHistory.appendChild(userMsg);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            window.parent.postMessage({'chat_message': message}, '*');
            chatInput.value = '';
        }
    }

    window.addEventListener('message', (event) => {
        if (event.data.chat_open !== undefined) {
            chatOpen = event.data.chat_open;
            chatWindow.classList.toggle('active', chatOpen);
        }
        if (event.data.chat_response) {
            const botMsg = document.createElement('p');
            botMsg.textContent = 'AI: ' + event.data.chat_response;
            chatHistory.appendChild(botMsg);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    });
    </script>
""", unsafe_allow_html=True)

if "chat_message" in st.session_state:
    message = st.session_state.chat_message
    if message:
        context = f"Current news: {st.session_state.current_news[:500]}"
        full_input = f"{context}\nUser: {message}"
        response = chatbot(full_input, max_length=150, num_return_sequences=1)[0]['generated_text']
        st.session_state.chat_history.append(f"You: {message}")
        st.session_state.chat_history.append(f"AI: {response}")
        st.session_state.chat_open = True
        st.markdown(f"""
            <script>
            window.parent.postMessage({{chat_response: "{response}"}}, '*');
            </script>
        """, unsafe_allow_html=True)
        del st.session_state.chat_message
        st.rerun()

st.text_input("Chat Input", key="chat_message", value="", help="Hidden input for chatbot", disabled=True)

st.markdown('</div>', unsafe_allow_html=True)