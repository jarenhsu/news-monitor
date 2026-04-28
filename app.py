import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import os
import json

# ============================================================
# 設定頁面
# ============================================================
st.set_page_config(
    page_title="資策會新聞熱度觀測站",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# Cyberpunk 樣式設定
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #0a0a1a 100%);
    color: #e0e0e0;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.glitch-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.8em;
    font-weight: 900;
    text-align: center;
    color: #00d4ff;
    text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff, 0 0 40px #00d4ff, 2px 2px 0px #ff006e, -2px -2px 0px #00ff88;
    letter-spacing: 4px;
    padding: 20px 0;
    animation: glitch 3s infinite;
}

@keyframes glitch {
    0%, 90%, 100% { text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff, 2px 2px 0px #ff006e; }
    92% { text-shadow: -2px 0 #ff006e, 2px 0 #00ff88, 0 0 20px #00d4ff; transform: translate(2px, 0); }
    94% { text-shadow: 2px 0 #ff006e, -2px 0 #00ff88, 0 0 20px #00d4ff; transform: translate(-2px, 0); }
    96% { text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff; transform: translate(0); }
}

.subtitle {
    font-family: 'Share Tech Mono', monospace;
    text-align: center;
    color: #00ff88;
    font-size: 0.9em;
    letter-spacing: 3px;
    margin-bottom: 30px;
}

.stat-card {
    background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,255,136,0.05));
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    margin: 5px;
}

.stat-number {
    font-family: 'Orbitron', monospace;
    font-size: 2.5em;
    font-weight: 700;
    color: #00d4ff;
    text-shadow: 0 0 15px #00d4ff;
}

.stat-label {
    font-family: 'Share Tech Mono', monospace;
    color: #888;
    font-size: 0.8em;
    letter-spacing: 2px;
    margin-top: 5px;
}

.section-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.2em;
    color: #ffd700;
    text-shadow: 0 0 10px #ffd700;
    border-left: 4px solid #ffd700;
    padding-left: 15px;
    margin: 25px 0 15px 0;
    letter-spacing: 2px;
}

.top-card {
    background: linear-gradient(135deg, rgba(255,215,0,0.08), rgba(255,140,0,0.05));
    border: 1px solid rgba(255,215,0,0.4);
    border-radius: 10px;
    padding: 18px 20px;
    margin: 10px 0;
    position: relative;
    box-shadow: 0 0 15px rgba(255,215,0,0.15), inset 0 0 15px rgba(255,215,0,0.03);
    transition: all 0.3s ease;
}

.top-card:hover {
    border-color: rgba(255,215,0,0.8);
    box-shadow: 0 0 25px rgba(255,215,0,0.3);
    transform: translateX(5px);
}

.normal-card {
    background: rgba(0,212,255,0.04);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 8px;
    padding: 14px 18px;
    margin: 7px 0;
    transition: all 0.3s ease;
}

.normal-card:hover {
    border-color: rgba(0,212,255,0.5);
    background: rgba(0,212,255,0.08);
    transform: translateX(3px);
}

.rank-number-top {
    font-family: 'Orbitron', monospace;
    font-size: 1.8em;
    font-weight: 900;
    color: #ffd700;
    text-shadow: 0 0 10px #ffd700;
    min-width: 50px;
    display: inline-block;
}

.rank-number-normal {
    font-family: 'Orbitron', monospace;
    font-size: 1.2em;
    font-weight: 700;
    color: #00d4ff;
    min-width: 40px;
    display: inline-block;
}

.news-title-top {
    font-size: 1.05em;
    color: #ffffff;
    font-weight: 600;
    line-height: 1.4;
}

.news-title-normal {
    font-size: 0.95em;
    color: #cccccc;
    line-height: 1.4;
}

.news-tag {
    display: inline-block;
    background: rgba(0,212,255,0.15);
    border: 1px solid rgba(0,212,255,0.3);
    color: #00d4ff;
    font-size: 0.7em;
    padding: 2px 8px;
    border-radius: 3px;
    margin: 3px 3px 0 0;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 1px;
}

.news-tag-keyword {
    background: rgba(255,215,0,0.1);
    border-color: rgba(255,215,0,0.3);
    color: #ffd700;
}

.heat-bar-container {
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
    height: 4px;
    margin-top: 8px;
    overflow: hidden;
}

.heat-bar {
    height: 100%;
    background: linear-gradient(90deg, #00d4ff, #00ff88);
    border-radius: 3px;
    box-shadow: 0 0 8px #00d4ff;
}

.media-list {
    font-family: 'Share Tech Mono', monospace;
    color: #888;
    font-size: 0.75em;
    margin-top: 5px;
}

.time-selector {
    background: rgba(0,212,255,0.05);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 10px;
    padding: 15px 20px;
    margin: 10px 0 20px 0;
    display: flex;
    align-items: center;
    gap: 15px;
}

.ai-analysis {
    background: linear-gradient(135deg, rgba(138,43,226,0.1), rgba(0,212,255,0.05));
    border: 1px solid rgba(138,43,226,0.4);
    border-radius: 10px;
    padding: 25px;
    margin: 20px 0;
    font-family: 'Share Tech Mono', monospace;
    color: #d0a0ff;
    line-height: 1.8;
    font-size: 0.9em;
}

.ai-title {
    font-family: 'Orbitron', monospace;
    color: #a855f7;
    text-shadow: 0 0 10px #a855f7;
    font-size: 1em;
    margin-bottom: 15px;
    letter-spacing: 2px;
}

.cyber-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff, transparent);
    margin: 20px 0;
}

.update-time {
    font-family: 'Share Tech Mono', monospace;
    color: #444;
    font-size: 0.75em;
    text-align: right;
    letter-spacing: 1px;
}

/* 時間選擇器樣式覆蓋 */
div[data-testid="stSelectbox"] > div {
    background: rgba(0,212,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    border-radius: 6px !important;
    color: #00d4ff !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 設定過濾清單
# ============================================================
BLOCKED_DOMAINS = [
    'find.org.tw', '104.com.tw', 'yes123.com.tw',
    'jobsdb.com', 'cake.me', 'linkedin.com'
]

# ============================================================
# 相似標題分群函數
# ============================================================
def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def group_similar_titles(df, threshold=0.3):
    titles = df['title'].tolist()
    sources = df['source'].tolist()
    urls = df['url'].tolist()
    groups = []
    used = set()

    for i, title_a in enumerate(titles):
        if i in used:
            continue
        group = [i]
        used.add(i)
        for j, title_b in enumerate(titles):
            if j in used:
                continue
            common_chars = set(title_a) & set(title_b)
            common_words = [c for c in common_chars if '\u4e00' <= c <= '\u9fff']
            if len(common_words) >= 4 or get_similarity(title_a, title_b) >= threshold:
                group.append(j)
                used.add(j)
        groups.append(group)

    result_rows = []
    for group in groups:
        group_titles = [titles[i] for i in group]
        group_sources = [sources[i] for i in group]
        group_urls = [urls[i] for i in group]

        rep_idx = max(range(len(group_titles)), key=lambda x: len(group_titles[x]))
        rep_title = group_titles[rep_idx]
        rep_url = group_urls[rep_idx]

        unique_sources = list(dict.fromkeys(group_sources))
        heat = len(unique_sources)

        orig_row = df.iloc[group[rep_idx]].copy()
        orig_row['title'] = rep_title
        orig_row['url'] = rep_url
        orig_row['heat'] = heat
        orig_row['media_list'] = ' · '.join(unique_sources)
        result_rows.append(orig_row)

    result_df = pd.DataFrame(result_rows)
    result_df = result_df.sort_values('heat', ascending=False).reset_index(drop=True)
    return result_df

# ============================================================
# 讀取 Google Sheets 資料（不含時間過濾，讓前端控制）
# ============================================================
@st.cache_data(ttl=3600)
def load_data():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        if os.path.exists('credentials.json'):
            creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
            SHEET_ID = '15AXNliucYP5-NTwleA4cSyoNhY-Fxyy1UBSCpxwCwlY'
        else:
            creds_json = st.secrets["GOOGLE_CREDENTIALS"]
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            SHEET_ID = st.secrets["SHEET_ID"]

        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet('raw_news')
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            return pd.DataFrame()

        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
        df = df[~df['source'].isin(BLOCKED_DOMAINS)]

        return df

    except Exception as e:
        st.error(f"資料載入失敗：{e}")
        return pd.DataFrame()

# ============================================================
# 主畫面
# ============================================================
st.markdown('<div class="glitch-title">📡 資策會新聞熱度觀測站</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">// INSTITUTE FOR INFORMATION INDUSTRY · NEWS MONITOR SYSTEM //</div>', unsafe_allow_html=True)
st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

# 時間範圍選擇器
col_sel1, col_sel2, col_sel3 = st.columns([1, 2, 1])
with col_sel2:
    days_option = st.selectbox(
        '📅 選擇分析區間',
        options=[7, 14, 30],
        index=2,
        format_func=lambda x: f'過去 {x} 天'
    )

st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

# 載入資料
with st.spinner('🔄 正在從資料庫讀取新聞...'):
    df_raw = load_data()

if df_raw.empty:
    st.warning("⚠️ 目前無資料，請確認 Google Sheets 連線與資料是否正常。")
    st.stop()

# 依選擇的天數過濾
cutoff = datetime.now() - timedelta(days=days_option)
df_filtered = df_raw[df_raw['published_at'] >= cutoff].copy()

if df_filtered.empty:
    st.warning(f"⚠️ 過去 {days_option} 天內無資料，請嘗試選擇更長的區間。")
    st.stop()

# 相似標題分群計算熱度
df = group_similar_titles(df_filtered, threshold=0.3)

# 統計數字
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number">{len(df)}</div>
        <div class="stat-label">📰 新聞事件數</div>
    </div>''', unsafe_allow_html=True)

with col2:
    total_media = df['media_list'].str.split(' · ').explode().nunique() if 'media_list' in df.columns else 0
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number">{total_media}</div>
        <div class="stat-label">📡 媒體來源數</div>
    </div>''', unsafe_allow_html=True)

with col3:
    top_keyword = df["keyword"].value_counts().index[0] if "keyword" in df.columns and len(df) > 0 else "N/A"
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number" style="font-size:1.5em">{top_keyword}</div>
        <div class="stat-label">🔥 最熱關鍵字</div>
    </div>''', unsafe_allow_html=True)

with col4:
    max_heat = int(df["heat"].max()) if "heat" in df.columns and len(df) > 0 else 0
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number">{max_heat}</div>
        <div class="stat-label">⚡ 最高媒體聲量</div>
    </div>''', unsafe_allow_html=True)

st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

# TOP 5
st.markdown(f'<div class="section-title">🏆 TOP 5 過去 {days_option} 天最熱新聞</div>', unsafe_allow_html=True)

top5 = df.head(5)
max_heat_val = top5['heat'].max() if len(top5) > 0 else 1

for i, row in top5.iterrows():
    rank = i + 1
    heat_pct = int((row['heat'] / max_heat_val) * 100)
    title = row.get('title', '無標題')
    url = row.get('url', '#')
    keyword = row.get('keyword', '')
    pub_date = str(row.get('published_at', ''))[:10]
    media_list = row.get('media_list', '')
    heat = int(row.get('heat', 1))

    st.markdown(f'''
    <div class="top-card">
        <div style="display:flex; align-items:flex-start; gap:15px;">
            <div class="rank-number-top">#{rank}</div>
            <div style="flex:1">
                <div class="news-title-top">
                    <a href="{url}" target="_blank" style="color:#ffffff; text-decoration:none;">
                        {title}
                    </a>
                </div>
                <div style="margin-top:8px;">
                    <span class="news-tag news-tag-keyword">🔑 {keyword}</span>
                    <span class="news-tag">📅 {pub_date}</span>
                    <span class="news-tag" style="color:#00ff88; border-color:#00ff88;">⚡ 聲量 {heat}</span>
                </div>
                <div class="media-list">📡 媒體：{media_list}</div>
                <div class="heat-bar-container">
                    <div class="heat-bar" style="width:{heat_pct}%"></div>
                </div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# TOP 6-10
st.markdown(f'<div class="section-title">📊 TOP 6-10 追蹤新聞</div>', unsafe_allow_html=True)

next5 = df.iloc[5:10]
for i, row in next5.iterrows():
    rank = i + 1
    title = row.get('title', '無標題')
    url = row.get('url', '#')
    keyword = row.get('keyword', '')
    media_list = row.get('media_list', '')
    heat = int(row.get('heat', 1))

    st.markdown(f'''
    <div class="normal-card">
        <div style="display:flex; align-items:center; gap:12px;">
            <div class="rank-number-normal">#{rank}</div>
            <div style="flex:1">
                <div class="news-title-normal">
                    <a href="{url}" target="_blank" style="color:#cccccc; text-decoration:none;">
                        {title}
                    </a>
                </div>
                <div style="margin-top:5px;">
                    <span class="news-tag news-tag-keyword">🔑 {keyword}</span>
                    <span class="news-tag">⚡ 聲量 {heat}</span>
                </div>
                <div class="media-list">📡 {media_list}</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

# AI 分析
st.markdown('<div class="section-title">🤖 AI 月度輿情分析</div>', unsafe_allow_html=True)

top_keywords = df['keyword'].value_counts().head(3).index.tolist() if 'keyword' in df.columns else []
top_news = df['title'].head(3).tolist()
top_media = df['media_list'].head(1).values[0] if len(df) > 0 else ''

analysis_text = f"""
▸ 系統分析期間：過去 {days_option} 天 · 新聞事件數：{len(df)} 則

▸ 本期最活躍關鍵字：{' · '.join(top_keywords) if top_keywords else 'N/A'}
  → 顯示資策會在上述議題持續受到媒體關注

▸ 最高聲量事件媒體列表：{top_media}

▸ 本期最熱事件 TOP 3：
  1. {top_news[0] if len(top_news) > 0 else 'N/A'}
  2. {top_news[1] if len(top_news) > 1 else 'N/A'}
  3. {top_news[2] if len(top_news) > 2 else 'N/A'}

▸ 綜合研判：
  本期資策會相關新聞以「{top_keywords[0] if top_keywords else '數位轉型'}」議題聲量最高，
  建議持續關注後續媒體動態，強化對外溝通策略。
"""

st.markdown(f'''
<div class="ai-analysis">
    <div class="ai-title">⚡ SYSTEM ANALYSIS · 智能輿情摘要</div>
    <pre style="font-family: Share Tech Mono, monospace; white-space: pre-wrap; margin:0;">{analysis_text}</pre>
</div>
''', unsafe_allow_html=True)

st.markdown(f'<div class="update-time">分析區間：過去 {days_option} 天 · 最後更新：{datetime.now().strftime("%Y-%m-%d %H:%M")} · 資料每小時自動更新</div>', unsafe_allow_html=True)