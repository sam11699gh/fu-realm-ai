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
    </style>
    """, unsafe_allow_html=True)

# --- 2. 診斷與讀取函數 (關鍵修正) ---
@st.cache_data
def load_and_fix_data(url, type_name):
    try:
        df = pd.read_csv(url)
        
        # 1. 強制清除所有標題的空白
        df.columns = df.columns.str.strip()
        
        # 2. 智慧模糊對應 (只要包含關鍵字就抓取)
        rename_map = {}
        for col in df.columns:
            # 針對 MBTI 與 脈輪的通用欄位
            if "題目" in col or "Question" in col:
                rename_map[col] = "Question"
            elif "模式" in col or "Mode" in col or "Type" in col:
                rename_map[col] = "Mode"
            elif "維度" in col or "Dimension" in col:
                rename_map[col] = "Dimension"
            elif "選項A" in col or "Option_A" in col or "Option A" in col:
                rename_map[col] = "Option_A"
            elif "選項B" in col or "Option_B" in col or "Option B" in col:
                rename_map[col] = "Option_B"
            elif "脈輪" in col or "Category" in col or "分類" in col:
                rename_map[col] = "Chakra_Category"
                
        df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ 無法讀取 {type_name} CSV。請檢查連結是否正確。錯誤訊息: {e}")
        return None

# --- 3. 初始化 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MBTI_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_URL = st.secrets["CHAKRA_CSV_URL"]
    genai.configure(api_key=API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-pro')
except:
    st.error("⚠️ Secrets 設定有誤，請檢查 Streamlit 後台。")
    st.stop()

# --- 4. 側邊欄 ---
with st.sidebar:
    st.title("✨ Fù Realm Debug Mode")
    if st.button("🔄 重置系統"):
        st.session_state.clear()
        st.rerun()

# --- 5. 主流程 ---

# A. 歡迎頁
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷")
    st.info("系統準備就緒，請選擇模式")
    
    # 預先載入檢查 (除錯關鍵)
    df_test = load_and_fix_data(MBTI_URL, "MBTI")
    if df_test is not None:
        required = ["Question", "Option_A", "Option_B", "Dimension"]
        missing = [c for c in required if c not in df_test.columns]
        if missing:
            st.error(f"⚠️ MBTI 題庫讀取異常！")
            st.write(f"**系統找到的欄位：** {list(df_test.columns)}")
            st.write(f"**缺少的欄位：** {missing}")
            st.stop()
            
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
    df = load_and_fix_data(MBTI_URL, "MBTI")
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
        dims = {'E/I':0, 'S/N':0, 'T/F':0, 'J/P':0}
        # 簡單計分
        res_df = pd.DataFrame(st.session_state.mbti_answers)
        
        # 防止空值錯誤
        if not res_df.empty and 'dim' in res_df.columns:
             final_mbti = ""
             for d in ['E / I', 'S / N', 'T / F', 'J / P']:
                 sub = res_df[res_df['dim'] == d]
                 a = (sub['score']=='A').sum()
                 b = (sub['score']=='B').sum()
                 final_mbti += d[0] if a >= b else d[4]
             st.session_state.mbti_res = final_mbti
        else:
             st.session_state.mbti_res = "INFJ" # 預設值防止崩潰
             
        st.session_state.step = "chakra_pre"; st.rerun()

# D. 脈輪前導
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI: {st.session_state.mbti_res}")
    c1, c2 = st.columns(2)
    if c1.button("⚡ 快速"): st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"; st.rerun()
    if c2.button("🔮 深度"): st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"; st.rerun()

# E. 脈輪測驗
elif st.session_state.step == "chakra_quiz":
    df_c = load_and_fix_data(CHAKRA_URL, "Chakra")
    
    # 除錯檢查
    if "Chakra_Category" not in df_c.columns:
        st.error("❌ 脈輪題庫找不到「分類」欄位。")
        st.write(f"系統讀到的欄位: {list(df_c.columns)}")
        st.stop()

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
