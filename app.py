import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 基礎配置與安全性讀取 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 自動讀取後台秘密 (Secrets)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MBTI_Q_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_Q_URL = st.secrets["CHAKRA_CSV_URL"]
except Exception as e:
    st.error("⚠️ 系統秘密設定錯誤，請檢查 Streamlit Secrets 設定。")
    st.stop()

# 配置 AI 引擎
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-pro')

# --- 2. 品牌視覺定義 ---
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3.5em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 狀態初始化 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

# --- 4. 側邊欄 (純品牌展示) ---
with st.sidebar:
    st.title("✨ Fù Realm")
    st.write("您的專屬能量顧問")
    st.divider()
    if st.button("🔄 重置測驗"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 5. 核心邏輯與測驗流程 ---
@st.cache_data
def load_csv(url):
    return pd.read_csv(url)

def calc_mbti(ans_list):
    df = pd.DataFrame(ans_list)
    res = ""
    for d in ['E / I', 'S / N', 'T / F', 'J / P']:
        sub = df[df['dim'] == d]
        a_count = (sub['score'] == 'A').sum()
        b_count = (sub['score'] == 'B').sum()
        res += d[0] if a_count >= b_count else d[4]
    return res

# 流程：歡迎頁
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷系統")
    st.subheader("開啟您的靈魂頻率探索之旅")
    st.write("請選擇您偏好的 MBTI 探索模式：")
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型"): 
        st.session_state.mbti_mode = "Known"; st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型"): 
        st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型"): 
        st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"; st.rerun()

# 流程：MBTI 測驗中
elif st.session_state.step == "mbti_quiz":
    df_m = load_csv(MBTI_Q_URL)
    qs = df_m if st.session_state.mbti_mode == "Deep" else df_m[df_m['Mode'].str.contains("探索")]
    idx = len(st.session_state.mbti_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.subheader(f"MBTI 測驗 ({idx+1}/{len(qs)})")
        st.progress((idx+1)/len(qs))
        st.markdown(f"**{row['Question']}**")
        if st.button(row['Option_A'], key=f"ma{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
        if st.button(row['Option_B'], key=f"mb{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
    else:
        st.session_state.mbti_res = calc_mbti(st.session_state.mbti_answers); st.session_state.step = "chakra_pre"; st.rerun()

# 流程：MBTI 輸入 (已知型)
elif st.session_state.step == "mbti_input":
    m = st.selectbox("請選擇您的 MBTI：", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("確認，進入脈輪掃描"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# 流程：脈輪測驗選擇
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI 分析完成：{st.session_state.mbti_res}")
    st.subheader("選擇脈輪檢測深度")
    col1, col2 = st.columns(2)
    if col1.button("⚡ 快速檢測 (14題)"):
        st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"; st.rerun()
    if col2.button("🔮 深度掃描 (56題)"):
        st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"; st.rerun()

# 流程：脈輪測驗中
elif st.session_state.step == "chakra_quiz":
    df_c = load_csv(CHAKRA_Q_URL)
    qs = df_c[df_c['Mode'].str.contains("快速")] if st.session_state.chakra_mode == "Quick" else df_c
    idx = len(st.session_state.chakra_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.subheader(f"脈輪掃描 ({idx+1}/{len(qs)})")
        st.progress((idx+1)/len(qs))
        st.markdown(f"**{row['Question']}**")
        score = st.select_slider("符合程度 (1不符合 -> 5非常符合)", options=[1, 2, 3, 4, 5], value=3, key=f"cs{idx}")
        if st.button("下一題", key=f"cb{idx}"):
            st.session_state.chakra_answers[idx] = {'cat': row['Chakra_Category'], 'val': score}; st.rerun()
    else:
        final_df = pd.DataFrame(st.session_state.chakra_answers).T
        st.session_state.chakra_res = final_df.groupby('cat')['val'].mean().to_dict()
        st.session_state.step = "result"; st.rerun()

# 流程：最終結果與 AI 報告
elif st.session_state.step == "result":
    st.title("🔮 您的能量診斷報告")
    # 雷達圖
    df_plot = pd.DataFrame(dict(r=list(st.session_state.chakra_res.values()), theta=list(st.session_state.chakra_res.keys())))
    fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
    fig.update_polars(radialaxis_range=[1, 5])
    st.plotly_chart(fig)
    
    if st.button("✨ 召喚 AI 生成深度處方報告"):
        with st.spinner("AI 正在感應您的能量頻率..."):
            prompt = f"你是Fù Realm水晶專家。用戶MBTI:{st.session_state.mbti_res}, 脈輪分數(1-5):{st.session_state.chakra_res}。請提供簡短能量分析、肯定語、推薦晶石。結尾請溫柔引導私訊IG截圖。"
            response = ai_model.generate_content(prompt)
            st.markdown(response.text)
            st.divider()
            st.link_button("📩 私訊專業顧問 (預約您的水晶)", "https://ig.me/m/tinting12o3/")

    if st.button("🔄 重新測驗"):
        st.session_state.step = "welcome"; st.rerun()
        
