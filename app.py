import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 系統配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 安全性設定：嘗試讀取 Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MBTI_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_URL = st.secrets["CHAKRA_CSV_URL"]
except:
    st.error("⚠️ 系統設定讀取失敗，請檢查 Streamlit Secrets。")
    st.stop()

# 檢查 API Key
if not API_KEY or "換成" in API_KEY:
    st.warning("⚠️ 請在 Streamlit Secrets 設定正確的 GEMINI_API_KEY。")
else:
    genai.configure(api_key=API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-pro')

# --- 2. 萬能讀取器 (自動翻譯標題) ---
@st.cache_data
def load_data_smart(url, type_name):
    try:
        # 嘗試讀取 CSV (處理編碼)
        try:
            df = pd.read_csv(url, encoding='utf-8')
        except:
            df = pd.read_csv(url, encoding='utf-8-sig') 

        # 1. 清除標題空白
        df.columns = df.columns.str.strip()
        
        # 2. 建立中英對照表 (讓程式看懂中文標題)
        rename_map = {}
        for col in df.columns:
            c = col.lower()
            if any(x in c for x in ["題目", "問題", "question"]): rename_map[col] = "Question"
            elif any(x in c for x in ["模式", "type", "mode"]): rename_map[col] = "Mode"
            elif any(x in c for x in ["維度", "dim"]): rename_map[col] = "Dimension"
            elif any(x in c for x in ["選項a", "option a", "option_a"]): rename_map[col] = "Option_A"
            elif any(x in c for x in ["選項b", "option b", "option_b"]): rename_map[col] = "Option_B"
            elif any(x in c for x in ["分類", "脈輪", "category", "chakra"]): rename_map[col] = "Chakra_Category"
        
        # 3. 執行翻譯
        df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ 讀取 {type_name} 失敗: {e}")
        return None

# --- 3. 介面美化 ---
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 程式邏輯 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

# 側邊欄
with st.sidebar:
    st.title("✨ Fù Realm")
    if st.button("🔄 重置系統"):
        st.session_state.clear(); st.rerun()

# 頁面 A: 歡迎
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷")
    st.info("請選擇您的探索模式：")
    
    # 預先載入測試 (若有錯直接顯示)
    df_check = load_data_smart(MBTI_URL, "MBTI")
    if df_check is not None and "Question" not in df_check.columns:
        st.error(f"⚠️ 標題對應失敗。系統讀到的標題: {list(df_check.columns)}")
        st.stop()

    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型"): st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型"): st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型"): st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"; st.rerun()

# 頁面 B: 已知型輸入
elif st.session_state.step == "mbti_input":
    m = st.selectbox("選擇您的 MBTI", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# 頁面 C: MBTI 測驗
elif st.session_state.step == "mbti_quiz":
    df = load_data_smart(MBTI_URL, "MBTI")
    # 過濾題目
    qs = df if st.session_state.mbti_mode == "Deep" else df[df['Mode'].astype(str).str.contains("探索", na=False)]
    
    idx = len(st.session_state.mbti_answers)
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        
        c1, c2 = st.columns(2)
        if c1.button(str(row['Option_A']), key=f"ma{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
        if c2.button(str(row['Option_B']), key=f"mb{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
    else:
        # 結算
        res_df = pd.DataFrame(st.session_state.mbti_answers)
        if not res_df.empty and 'dim' in res_df.columns:
            final_mbti = ""
            for d in ['E / I', 'S / N', 'T / F', 'J / P']:
                sub = res_df[res_df['dim'] == d]
                a = (sub['score']=='A').sum()
                b = (sub['score']=='B').sum()
                final_mbti += d[0] if a >= b else d[4]
            st.session_state.mbti_res = final_mbti
        else:
            st.session_state.mbti_res = "INFJ" # 預設防止報錯
        st.session_state.step = "chakra_pre"; st.rerun()

# 頁面 D: 脈輪前導
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI 分析結果: {st.session_state.mbti_res}")
    c1, c2 = st.columns(2)
    if c1.button("⚡ 快速檢測"): st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"; st.rerun()
    if c2.button("🔮 深度檢測"): st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"; st.rerun()

# 頁面 E: 脈輪測驗
elif st.session_state.step == "chakra_quiz":
    df_c = load_data_smart(CHAKRA_URL, "Chakra")
    
    # 過濾題目
    qs = df_c[df_c['Mode'].astype(str).str.contains("快速", na=False)] if st.session_state.chakra_mode == "Quick" else df_c
    
    idx = len(st.session_state.chakra_answers)
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        val = st.slider("符合程度 (1-5)", 1, 5, 3, key=f"c{idx}")
        if st.button("下一題"):
            st.session_state.chakra_answers[idx] = {'cat': row['Chakra_Category'], 'val': val}
            st.rerun()
    else:
        # 結算
        res_df = pd.DataFrame(st.session_state.chakra_answers).T
        st.session_state.chakra_res = res_df.groupby('cat')['val'].mean().to_dict()
        st.session_state.step = "result"; st.rerun()

# 頁面 F: 結果報告
elif st.session_state.step == "result":
    st.title("🔮 您的靈魂能量報告")
    
    # 雷達圖
    if st.session_state.chakra_res:
        df_plot = pd.DataFrame(dict(r=list(st.session_state.chakra_res.values()), theta=list(st.session_state.chakra_res.keys())))
        fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
        fig.update_polars(radialaxis_range=[0, 5])
        st.plotly_chart(fig)
    
    if st.button("✨ 召喚 AI 顧問解讀"):
        if not API_KEY or "換成" in API_KEY:
             st.error("API Key 未設定正確")
        else:
            with st.spinner("AI 正在連結水晶能量場..."):
                prompt = f"客戶MBTI: {st.session_state.mbti_res}, 脈輪分數: {st.session_state.chakra_res}。請以 Fù Realm 水晶顧問口吻，給出短評、一句能量金句，並推薦一款水晶。結尾請引導私訊 IG: tinting12o3 截圖領取優惠。"
                try:
                    res = ai_model.generate_content(prompt)
                    st.markdown(res.text)
                    st.link_button("📩 私訊領取專屬水晶", "https://ig.me/m/tinting12o3/")
                except Exception as e:
                    st.error(f"AI 連線忙碌中: {e}")

    if st.button("🔄 重新測驗"):
        st.session_state.clear(); st.rerun()
