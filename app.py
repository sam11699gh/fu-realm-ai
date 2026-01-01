import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 系統配置與 Secrets 讀取 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 嘗試從後台 Secrets 獲取金鑰與連結
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MBTI_Q_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_Q_URL = st.secrets["CHAKRA_CSV_URL"]
except Exception as e:
    st.error("⚠️ 系統連線錯誤：請檢查 Streamlit Secrets 設定是否完整。")
    st.stop()

# 配置 AI
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-pro')

# --- 2. 品牌視覺美化 (金色系) ---
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化 Session State (記憶體) ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

# --- 4. 側邊欄 (乾淨版：只留品牌與重置) ---
with st.sidebar:
    st.title("✨ Fù Realm")
    st.write("您的專屬能量顧問")
    st.info("透過 AI 掃描您的靈魂頻率")
    st.divider()
    if st.button("🔄 重置所有進度"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 5. 核心邏輯函數 ---
@st.cache_data
def load_csv(url):
    try: return pd.read_csv(url)
    except: return None

def calc_mbti(ans_list):
    # 簡單的 MBTI 計算邏輯
    df = pd.DataFrame(ans_list)
    res = ""
    for d in ['E / I', 'S / N', 'T / F', 'J / P']:
        sub = df[df['dim'] == d]
        if not sub.empty:
            a_count = (sub['score'] == 'A').sum()
            b_count = (sub['score'] == 'B').sum()
            res += d[0] if a_count >= b_count else d[4]
        else:
            res += "-" # 避免無資料時報錯
    return res

# --- 6. 測驗流程控制 ---

# A. 歡迎頁
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷系統")
    st.subheader("探索您的內在人格與脈輪能量")
    st.write("請選擇您想開始的方式：")
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型\n(直接輸入)"): 
        st.session_state.mbti_mode = "Known"; st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型\n(20題測驗)"): 
        st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型\n(60題掃描)"): 
        st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"; st.rerun()

# B. MBTI 輸入 (已知型)
elif st.session_state.step == "mbti_input":
    m = st.selectbox("請選擇您的 MBTI：", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步：脈輪檢測"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# C. MBTI 測驗 (探索/深層)
elif st.session_state.step == "mbti_quiz":
    df_m = load_csv(MBTI_Q_URL)
    if df_m is not None:
        qs = df_m if st.session_state.mbti_mode == "Deep" else df_m[df_m['Mode'].str.contains("探索")]
        idx = len(st.session_state.mbti_answers)
        
        if idx < len(qs):
            row = qs.iloc[idx]
            st.subheader(f"MBTI 分析中 ({idx+1}/{len(qs)})")
            st.progress((idx+1)/len(qs))
            st.markdown(f"**{row['Question']}**")
            if st.button(row['Option_A'], key=f"ma{idx}"):
                st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
            if st.button(row['Option_B'], key=f"mb{idx}"):
                st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
        else:
            st.session_state.mbti_res = calc_mbti(st.session_state.mbti_answers)
            st.session_state.step = "chakra_pre"; st.rerun()

# D. 脈輪模式選擇
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI 分析完成：{st.session_state.mbti_res}")
    st.subheader("第二階段：能量脈輪掃描")
    col1, col2 = st.columns(2)
    if col1.button("⚡ 快速檢測 (14題)"):
        st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"; st.rerun()
    if col2.button("🔮 深度掃描 (56題)"):
        st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"; st.rerun()

# E. 脈輪測驗執行
elif st.session_state.step == "chakra_quiz":
    df_c = load_csv(CHAKRA_Q_URL)
    if df_c is not None:
        qs = df_c[df_c['Mode'].str.contains("快速")] if st.session_state.chakra_mode == "Quick" else df_c
        idx = len(st.session_state.chakra_answers)
        
        if idx < len(qs):
            row = qs.iloc[idx]
            st.subheader(f"脈輪能量掃描 ({idx+1}/{len(qs)})")
            st.progress((idx+1)/len(qs))
            st.markdown(f"**{row['Question']}**")
            val = st.select_slider("符合程度", options=[1,2,3,4,5], value=3, key=f"cs{idx}")
            if st.button("下一題", key=f"cb{idx}"):
                st.session_state.chakra_answers[idx] = {'cat': row['Chakra_Category'], 'val': val}; st.rerun()
        else:
            # 結算脈輪分數
            final_df = pd.DataFrame(st.session_state.chakra_answers).T
            st.session_state.chakra_res = final_df.groupby('cat')['val'].mean().to_dict()
            st.session_state.step = "result"; st.rerun()

# F. 最終報告與 AI 生成
elif st.session_state.step == "result":
    st.title("🔮 您的靈魂能量報告")
    st.write(f"MBTI 類型: **{st.session_state.mbti_res}**")
    
    # 雷達圖
    if st.session_state.chakra_res:
        df_plot = pd.DataFrame(dict(r=list(st.session_state.chakra_res.values()), theta=list(st.session_state.chakra_res.keys())))
        fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
        fig.update_polars(radialaxis_range=[0, 5])
        st.plotly_chart(fig)
    
    # AI 按鈕
    if st.button("✨ 召喚 AI 生成詳細處方 (含水晶推薦)"):
        with st.spinner("正在連結 Fù Realm 能量數據庫..."):
            prompt = f"""
            你現在是 'Fù Realm' 品牌的水晶療癒顧問。
            客戶資料：
            - MBTI: {st.session_state.mbti_res}
            - 脈輪狀態 (1-5分): {st.session_state.chakra_res}
            
            任務：
            1. 分析該 MBTI 與當前脈輪強弱點的關聯。
            2. 給予一句溫暖的能量肯定語。
            3. 推薦 1-2 種適合的水晶（請參考一般水晶學知識）。
            4. 最後必須加上這句話引導私訊：
               '👉 想要這款專屬水晶嗎？請截圖此畫面，點擊下方按鈕私訊我們，輸入【我要領取能量處方】，即可獲得專屬優惠！'
            """
            try:
                response = ai_model.generate_content(prompt)
                st.markdown(response.text)
                st.divider()
                st.link_button("📩 私訊 Fù Realm 顧問 (領取專屬水晶)", "https://ig.me/m/tinting12o3/")
            except Exception as e:
                st.error(f"AI 連線忙碌中，請稍後再試。({str(e)})")

    if st.button("🔄 重新測驗"):
        st.session_state.step = "welcome"; st.rerun()
