import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 基礎網頁配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 自定義 CSS 讓介面更精美
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 初始化 Session State (儲存使用者進度)
if "step" not in st.session_state:
    st.session_state.step = "welcome"
if "mbti_type" not in st.session_state:
    st.session_state.mbti_type = None

# --- 2. 側邊欄設定 (請在此輸入您的資料) ---
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=Fu+Realm", width=100) # 建議換成您的品牌 Logo 連結
    st.title("🛡️ 顧問設定面板")
    user_api_key = st.text_input("Gemini API Key", type="password", help="請輸入從 Google AI Studio 取得的 Key")
    # 這裡預留給您的 Google Sheet CSV 連結，之後您可以直接貼在下方
    csv_url = st.text_input("Google Sheet CSV 連結", placeholder="請貼上發布為網頁的 CSV 網址")
    
    st.divider()
    st.info("48小時快速部署版 v1.0")

# 配置 AI
if user_api_key:
    genai.configure(api_key=user_api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

# --- 3. 網頁邏輯流程 ---

# A. 歡迎頁面
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷系統")
    st.subheader("探索您的內在人格與脈輪能量")
    st.write("請選擇您想開始的方式：")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 已知型\n(我有 MBTI)"):
            st.session_state.entry_mode = "Known"
            st.session_state.step = "select_mbti"
    with col2:
        if st.button("🔍 探索型\n(20題測驗)"):
            st.session_state.entry_mode = "Explore"
            st.session_state.step = "mbti_test"
    with col3:
        if st.button("💎 深層型\n(60題靈魂掃描)"):
            st.session_state.entry_mode = "Deep"
            st.session_state.step = "mbti_test"

# B. 已知型：直接選 MBTI
elif st.session_state.step == "select_mbti":
    st.header("您的人格特質")
    mbti = st.selectbox("請選擇您的 MBTI：", ["INTJ", "INFP", "ENFJ", "ENTP", "ISTJ", "ISFP", "ESTP", "ESFJ", "INFJ", "ENTJ", "INTP", "ENFP", "ISTP", "ISFJ", "ESTJ", "ESFP"])
    if st.button("確認，進入脈輪測驗"):
        st.session_state.mbti_type = mbti
        st.session_state.step = "chakra_test"

# C. 測驗型 (MBTI 測驗中...)
elif st.session_state.step == "mbti_test":
    st.header(f"正在進行 {st.session_state.entry_mode} 測驗")
    st.progress(30) # 示意進度條
    st.write("*(這裡會根據您的分頁 5 抓取題目)*")
    if st.button("完成測驗，看結果"):
        st.session_state.mbti_type = "INFJ" # 示意結果
        st.session_state.step = "chakra_test"

# D. 脈輪測驗結果 (雷達圖)
elif st.session_state.step == "chakra_test":
    st.header(f"您的能量雷達圖 (MBTI: {st.session_state.mbti_type})")
    
    # 模擬數據 (正式版將從題目計算)
    scores = {"海底輪": 40, "臍輪": 75, "太陽輪": 30, "心輪": 85, "喉輪": 50, "眉心輪": 65, "頂輪": 60}
    
    df_radar = pd.DataFrame(dict(r=list(scores.values()), theta=list(scores.keys())))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig)

    if st.button("生成 AI 完整處方報告"):
        st.session_state.step = "report"

# E. 最終報告
elif st.session_state.step == "report":
    st.header("🔮 Crystal Rx 專屬處方")
    st.success(f"分析完成！身為 {st.session_state.mbti_type} 的您...")
    
    st.markdown("""
    ### 🌿 能量狀態分析
    您目前的 **心輪** 能量最穩定，但在 **太陽輪** 有所阻塞，這可能導致您雖然有豐富理想卻缺乏行動力。
    
    ### 💎 首選晶石建議
    - **黃水晶 / 虎眼石**：增強意志力。
    - **黑曜石**：幫助能量落地。
    
    [👉 前往 Fù Realm 賣場選購您的專屬水晶](https://instagram.com/furealm)
    """)
    if st.button("重新測試"):
        st.session_state.step = "welcome"
