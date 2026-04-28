import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import os
import json

st.set_page_config(
    page_title="資策會新聞熱度觀測站",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
</style>
""", unsafe_allow_html=True)

# ============================================================
# 設定過濾清單
# ============================================================
BLOCKED_DOMAINS = [
    'find.org.tw', '104.com.tw', 'yes123.com.tw',
    'jobsdb.com', 'cake.me', 'linkedin.com'
]

KEY_COMBINATIONS = [
    ['奇美', '資策會'],
    ['奇美', '醫療AI'],
    ['奇美', '職能護照'],
    ['奇美', 'AI人才'],
    ['奇美', '醫療'],
    ['高虹安', '論文'],
    ['高虹安', '抄襲'],
    ['高虹安', '資策會'],
    ['高虹安', '期刊'],
    ['ITS', '資策會'],
    ['數位轉型', '資策會'],
    ['職能護照', '醫療'],
]

def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def share_key_combination(a, b):
    for combo in KEY_COMBINATIONS:
        if all(word in a for word in combo) and all(word in b for word in combo):
            return True
    return False

def group_similar_titles(df, threshold=0.3):
    titles = df['title'].tolist()
    sources = df['source'].tolist()
    urls = df['url'].tolist()
    media_lists = df['media_list'].tolist() if 'media_list' in df.columns else [s for s in sources]

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
            similarity = get_similarity(title_a, title_b)
            same_combo = share_key_combination(title_a, title_b)

            if len(common_words) >= 6 or similarity >= threshold or same_combo:
                group.append(j)
                used.add(j)

        groups.append(group)

    result_rows = []
    for group in groups:
        group_titles = [titles[i] for i in group]
        group_urls = [urls[i] for i in group]

        all_sources = []
        for i in group:
            media = media_lists[i]
            if ' · ' in str(media):
                all_sources.extend(media.split(' · '))
            else:
                all_sources.append(str(media))

        unique_sources = list(dict.fromkeys([s for s in all_sources if s and s != 'nan']))
        heat = len(unique_sources)

        rep_idx = max(range(len(group_titles)), key=lambda x: len(group_titles[x]))
        rep_title = group_titles[rep_idx]
        rep_url = group_urls[rep_idx]

        orig_row = df.iloc[group[rep_idx]].copy()
        orig_row['title'] = rep_title
        orig_row['url'] = rep_url
        orig_row['heat'] = heat
        orig_row['media_list'] = ' · '.join(unique_sources)
        result_rows.append(orig_row)

    result_df = pd.DataFrame(result_rows)
    result_df = result_df.sort_values('heat', ascending=False).reset_index(drop=True)
    return result_df

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
        df = df[df['title'].str.contains('資策會', na=False)]
        df = df.drop_duplicates(subset=['title'], keep='first')

        return df

    except Exception as e:
        st.error(f"資料載入失敗：{e}")
        return pd.DataFrame()

# ============================================================
# 英雄區塊（Canvas 旋轉光暈）
# ============================================================
components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: transparent; overflow: hidden; }

  .hero {
    position: relative;
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  canvas {
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
  }

  .hero-title {
    position: relative;
    z-index: 10;
    font-family: 'Orbitron', monospace;
    font-size: 2.2em;
    font-weight: 900;
    color: #ffffff;
    text-shadow:
      0 0 20px rgba(0,212,255,0.9),
      0 0 40px rgba(0,212,255,0.5),
      0 2px 8px rgba(0,0,0,0.9);
    letter-spacing: 3px;
    text-align: center;
    padding: 0 20px;
  }

  .hero-sub {
    position: relative;
    z-index: 10;
    font-family: 'Share Tech Mono', monospace;
    color: rgba(0,255,136,0.95);
    font-size: 0.75em;
    letter-spacing: 3px;
    margin-top: 14px;
    text-shadow: 0 0 12px rgba(0,255,136,0.7);
    text-align: center;
    padding: 0 20px;
  }
</style>
</head>
<body>
  <div class="hero">
    <canvas id="c"></canvas>
    <div class="hero-title">📡 資策會新聞熱度觀測站</div>
    <div class="hero-sub">// INSTITUTE FOR INFORMATION INDUSTRY · NEWS MONITOR SYSTEM //</div>
  </div>

  <script>
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');

    function resize() {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    // 定義旋轉光球
    const orbs = [
      { baseX: 0.25, baseY: 0.5, r: 160, color: '0,212,255',   speed: 1.2, angle: 0,   orbitX: 0.22, orbitY: 0.28 },
      { baseX: 0.75, baseY: 0.5, r: 140, color: '168,85,247',  speed: 0.9, angle: 2.1, orbitX: 0.18, orbitY: 0.32 },
      { baseX: 0.5,  baseY: 0.5, r: 120, color: '255,215,0',   speed: 1.5, angle: 4.2, orbitX: 0.28, orbitY: 0.22 },
      { baseX: 0.5,  baseY: 0.3, r: 100, color: '0,255,136',   speed: 1.0, angle: 1.0, orbitX: 0.15, orbitY: 0.20 },
    ];

    let last = 0;

    function draw(ts) {
      const dt = (ts - last) / 1000;
      last = ts;

      const W = canvas.width;
      const H = canvas.height;

      ctx.clearRect(0, 0, W, H);

      orbs.forEach(o => {
        o.angle += o.speed * dt;

        const cx = W * o.baseX + Math.cos(o.angle) * W * o.orbitX;
        const cy = H * o.baseY + Math.sin(o.angle * 0.7) * H * o.orbitY;

        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, o.r);
        grad.addColorStop(0, `rgba(${o.color}, 0.55)`);
        grad.addColorStop(0.5, `rgba(${o.color}, 0.2)`);
        grad.addColorStop(1, `rgba(${o.color}, 0)`);

        ctx.beginPath();
        ctx.arc(cx, cy, o.r, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      });

      requestAnimationFrame(draw);
    }

    requestAnimationFrame(draw);
  </script>
</body>
</html>
""", height=210)

# ============================================================
# 主畫面
# ============================================================
st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

col_sel1, col_sel2, col_sel3 = st.columns([1, 2, 1])
with col_sel2:
    period_option = st.selectbox(
        '📅 選擇分析區間',
        options=['過去 7 天', '過去 30 天', '今年'],
        index=0
    )

if period_option == '過去 7 天':
    cutoff = datetime.now() - timedelta(days=7)
    period_label = '過去 7 天'
elif period_option == '過去 30 天':
    cutoff = datetime.now() - timedelta(days=30)
    period_label = '過去 30 天'
else:
    cutoff = datetime(datetime.now().year, 1, 1)
    period_label = f'{datetime.now().year} 年全年'

st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

with st.spinner('🔄 正在從資料庫讀取新聞...'):
    df_raw = load_data()

if df_raw.empty:
    st.warning("⚠️ 目前無資料，請確認 Google Sheets 連線與資料是否正常。")
    st.stop()

df_filtered = df_raw[df_raw['published_at'] >= cutoff].copy()

if df_filtered.empty:
    st.warning(f"⚠️ {period_label} 內無資料，請嘗試選擇更長的區間。")
    st.stop()

df = group_similar_titles(df_filtered, threshold=0.3)
df = group_similar_titles(df, threshold=0.3)

# 統計數字
col1, col2 = st.columns(2)
with col1:
    total_media = df['media_list'].str.split(' · ').explode().nunique() if 'media_list' in df.columns else 0
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number">{total_media}</div>
        <div class="stat-label">📡 媒體來源數</div>
    </div>''', unsafe_allow_html=True)

with col2:
    max_heat = int(df["heat"].max()) if "heat" in df.columns and len(df) > 0 else 0
    st.markdown(f'''
    <div class="stat-card">
        <div class="stat-number">{max_heat}</div>
        <div class="stat-label">⚡ 最高媒體聲量</div>
    </div>''', unsafe_allow_html=True)

st.markdown('<hr class="cyber-divider">', unsafe_allow_html=True)

# TOP 5
st.markdown(f'<div class="section-title">🏆 TOP 5 · {period_label} 最熱新聞</div>', unsafe_allow_html=True)

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
st.markdown(f'<div class="section-title">📊 TOP 6-10 · 追蹤新聞</div>', unsafe_allow_html=True)

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

# 智慧輿情分析
st.markdown('<div class="section-title">🤖 智慧輿情分析</div>', unsafe_allow_html=True)

top_news = df['title'].head(3).tolist()
top_media = df['media_list'].head(1).values[0] if len(df) > 0 else ''
top_sources = df['media_list'].str.split(' · ').explode().value_counts().head(3).index.tolist() if 'media_list' in df.columns else []

analysis_text = f"""
▸ 最高聲量事件媒體列表：{top_media}

▸ 本期最熱事件 TOP 3：
  1. {top_news[0] if len(top_news) > 0 else 'N/A'}
  2. {top_news[1] if len(top_news) > 1 else 'N/A'}
  3. {top_news[2] if len(top_news) > 2 else 'N/A'}

▸ 主要報導媒體：{' · '.join(top_sources) if top_sources else 'N/A'}

▸ 綜合研判：
  {period_label}內資策會共獲得 {len(df)} 則媒體事件關注，
  最高單一事件聲量達 {max_heat} 家媒體報導，
  建議持續關注後續媒體動態，強化對外溝通策略。
"""

st.markdown(f'''
<div class="ai-analysis">
    <div class="ai-title">⚡ SYSTEM ANALYSIS · 智慧輿情摘要</div>
    <pre style="font-family: Share Tech Mono, monospace; white-space: pre-wrap; margin:0;">{analysis_text}</pre>
</div>
''', unsafe_allow_html=True)

st.markdown(f'<div class="update-time">分析區間：{period_label} · 最後更新：{datetime.now().strftime("%Y-%m-%d %H:%M")} · 資料每日自動更新</div>', unsafe_allow_html=True)