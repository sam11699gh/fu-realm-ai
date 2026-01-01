import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 系統配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# CSS 美化
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# 讀取 Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MBTI_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_URL = st.secrets["CHAKRA_CSV_URL"]
    genai.configure(api_key=API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    st.error(f"⚠️ Secrets 設定錯誤: {e}")
    st.stop()

# --- 2. 萬能讀取與診斷函數 (關鍵修正) ---
@st.cache_data
def load_data_safe(url, data_type):
    # 嘗試多種編碼，解決 Excel 亂碼問題
    encodings = ['utf-8', 'utf-8-sig', 'big5', 'cp950']
    df = None
    
    for enc in encodings:
        try:
            df = pd.read_csv(url, encoding=enc)
            # 如果成功讀取且沒有亂碼(簡單檢查)，就跳出迴圈
            if len(df.columns) > 1:
                break
        except:
            continue
            
    if df is None:
        st.error(f"❌ 無法讀取 {data_type} CSV。請檢查連結是否正確。")
        return None

    # 清除欄位空白
    df.columns = df.columns.str.strip()
    
    # 自動欄位對應 (Auto-Mapping)
    rename_map = {}
    for col in df.columns:
        c = col.lower() # 轉小寫比對
        if "題" in c or "question" in c: rename_map[col] = "Question"
        elif "模" in c or "mode" in c or "type" in c: rename_map[col] = "Mode"
        elif "維" in c or "dim" in c: rename_map[col] = "Dimension"
        elif "a" in c and ("option" in c or "項" in c): rename_map[col] = "Option_A"
        elif "b" in c and ("option" in c or "項" in c): rename_map[col] = "Option_B"
        elif "脈" in c or "cat" in c or "分" in c: rename_map[col] = "Chakra_Category"
            
    df.rename(columns=rename_map, inplace=True)
    return df

def check_columns(df, required_cols, name):
    # 檢查是否缺欄位，缺的話直接顯示在螢幕上
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"⚠️ {name} 題庫欄位對應失敗！")
        st.write(f"❌ 缺少的欄位: {missing}")
        st.write(f"👀 系統讀到的欄位 (請檢查是否亂碼): {list(df.columns)}")
        st.stop() # 強制暫停，避免後面報錯

# --- 3. 初始化 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("✨ Fù Realm")
    if st.button("🔄 重置系統"):
        st.session_state.clear(); st.rerun()

# --- 5. 主流程 ---

# A. 歡迎頁
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷")
    st.info("系統準備就緒，請選擇模式")
    
    # 預先載入測試 (若有錯直接顯示)
    df_test = load_data_safe(MBTI_URL, "MBTI")
    if df_test is not None:
        check_columns(df_test, ["Question", "Option_A", "Option_B", "Dimension"], "MBTI")

    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型"): st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型"): st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型"): st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"; st.rerun()

# B. MBTI 輸入
elif st.session_state.step == "mbti_input":
    m = st.selectbox("選擇 MBTI", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# C. MBTI 測驗
elif st.session_state.step == "mbti_quiz":
    df = load_data_safe(MBTI_URL, "MBTI")
    # 再次檢查確保萬無一失
    check_columns(df, ["Question", "Option_A", "Option_B", "Dimension"], "MBTI")

    qs = df if st.session_state.mbti_mode == "Deep" else df[df['Mode'].astype(str).str.contains("探索", na=False)]
    
    idx = len(st.session_state.mbti_answers)
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        
        c1, c2 = st.columns(2)
        if c1.button(str(row['Option_A']), key=f"a{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
        if c2.button(str(row['Option_B']), key=f"b{idx}"):
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
    else:
        # 計算結果
        res_df = pd.DataFrame(st.session_state.mbti_answers)
        final_mbti = ""
        for d in ['E / I', 'S / N', 'T / F', 'J / P']:
             if 'dim' in res_df.columns:
                 sub = res_df[res_df['dim'] == d]
                 a = (sub['score']=='A').sum()
                 b = (sub['score']=='B').sum()
                 final_mbti += d[0] if a >= b else d[4]
             else:
                 final_mbti = "INFJ" # Fallback
        st.session_state.mbti_res = final_mbti
        st.session_state.step = "chakra_pre"; st.rerun()

# D. 脈輪前導
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI: {st.session_state.mbti_res}")
    c1, c2 = st.columns(2)
    if c1.button("⚡ 快速"): st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"; st.rerun()
    if c2.button("🔮 深度"): st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"; st.rerun()

# E. 脈輪測驗
elif st.session_state.step == "chakra_quiz":
    df_c = load_data_safe(CHAKRA_URL, "Chakra")
    check_columns(df_c, ["Question", "Chakra_Category"], "Chakra")

    qs = df_c[df_c['Mode'].astype(str).str.contains("快速", na=False)] if st.session_state.chakra_mode == "Quick" else df_c
    idx = len(st.session_state.chakra_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.subheader(f"Q{idx+1}: {row['Question']}")
        val = st.slider("符合程度", 1, 5, 3, key=f"c{idx}")
        if st.button("下一題"):
            st.session_state.chakra_answers[idx] = {'cat': row['Chakra_Category'], 'val': val}
            st.rerun()
    else:
        res_df = pd.DataFrame(st.session_state.chakra_answers).T
        st.session_state.chakra_res = res_df.groupby('cat')['val'].mean().to_dict()
        st.session_state.step = "result"; st.rerun()

# F. 結果
elif st.session_state.step == "result":
    st.title("🔮 診斷報告")
    
    df_plot = pd.DataFrame(dict(r=list(st.session_state.chakra_res.values()), theta=list(st.session_state.chakra_res.keys())))
    fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
    st.plotly_chart(fig)
    
    if st.button("生成 AI 報告"):
        with st.spinner("AI 分析中..."):
            prompt = f"客戶 MBTI: {st.session_state.mbti_res}, 脈輪: {st.session_state.chakra_res}。請以 Fù Realm 專家身分推薦水晶並給予建議。結尾引導私訊 IG: tinting12o3 領取優惠。"
            try:
                res = ai_model.generate_content(prompt)
                st.markdown(res.text)
                st.link_button("📩 私訊領取優惠", "https://ig.me/m/tinting12o3/")
            except Exception as e:
                st.error(f"AI Error: {e}")

    if st.button("重測"):
        st.session_state.clear(); st.rerun()
