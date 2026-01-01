import streamlit as st
import pandas as pd
import plotly.express as px
import random

# --- 1. 系統配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 讀取網址
try:
    MBTI_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_URL = st.secrets["CHAKRA_CSV_URL"]
    PRODUCT_URL = st.secrets.get("PRODUCT_CSV_URL", "") 
    LOGIC_URL = st.secrets.get("LOGIC_CSV_URL", "")
except:
    st.error("⚠️ 系統設定讀取失敗，請檢查 Streamlit Secrets。")
    st.stop()

# --- 2. 萬能讀取器 ---
@st.cache_data
def load_data_smart(url, type_name):
    if not url: return None
    try:
        try: df = pd.read_csv(url, encoding='utf-8')
        except: df = pd.read_csv(url, encoding='utf-8-sig') 
        
        df.columns = df.columns.str.strip()
        rename_map = {}
        for col in df.columns:
            c = col.lower().replace("_", "").replace(" ", "")
            if any(x in c for x in ["題目", "問題", "question", "content"]): rename_map[col] = "Question"
            elif any(x in c for x in ["模式", "type", "mode"]): rename_map[col] = "Mode"
            elif any(x in c for x in ["維度", "dim"]): rename_map[col] = "Dimension"
            elif "optiona" in c or "選項a" in c: rename_map[col] = "Option_A"
            elif "optionb" in c or "選項b" in c: rename_map[col] = "Option_B"
            elif any(x in c for x in ["分類", "脈輪", "category", "chakra", "focus"]): rename_map[col] = "Chakra_Category"
            elif "product" in c or "商品" in c: rename_map[col] = "Product_Name"
            elif "gem" in c or "晶石" in c or "stone" in c: rename_map[col] = "Preferred_Gemstones"
            elif "link" in c or "連結" in c or "url" in c: rename_map[col] = "Store_Link"
            elif "mbti" in c and "match" in c: rename_map[col] = "MBTI_Match"
            elif "status" in c or "狀態" in c or "range" in c or "score" in c: rename_map[col] = "Status"
            elif "desc" in c or "說明" in c or "定義" in c: rename_map[col] = "Description"
            elif "advice" in c or "建議" in c: rename_map[col] = "Advice"

        df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        return None

# --- 3. CSS 優化 ---
st.markdown("""
    <style>
    .report-card { 
        background-color: #ffffff !important; 
        color: #333333 !important;
        padding: 20px; 
        border-radius: 10px; 
        border-left: 8px solid #d4af37; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }
    .report-card h3 { color: #d4af37 !important; }
    .report-card p { color: #555555 !important; }
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 狀態管理 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = "INFJ"
    st.session_state.chakra_res = {}
    st.session_state.current_questions = []

# 抽題邏輯
def draw_questions(df, type_col, categories, count_per_cat):
    selected_indices = []
    for cat in categories:
        subset = df[df[type_col] == cat]
        if not subset.empty:
            n = min(len(subset), count_per_cat)
            selected = subset.sample(n=n)
            selected_indices.extend(selected.index.tolist())
    random.shuffle(selected_indices)
    return df.loc[selected_indices].reset_index(drop=True)

# 側邊欄
with st.sidebar:
    st.title("✨ Fù Realm")
    if st.button("🔄 重置系統"):
        st.session_state.clear(); st.rerun()

# 頁面 A: 歡迎
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷")
    st.info("數據化靈魂解讀：MBTI x 脈輪能量")
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型"): st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型"): 
        st.session_state.mbti_mode = "Explore"
        st.session_state.current_questions = []
        st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型"): 
        st.session_state.mbti_mode = "Deep"
        st.session_state.current_questions = []
        st.session_state.step = "mbti_quiz"; st.rerun()

# 頁面 B: 已知型輸入
elif st.session_state.step == "mbti_input":
    m = st.selectbox("選擇您的 MBTI", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# 頁面 C: MBTI 測驗
elif st.session_state.step == "mbti_quiz":
    if not isinstance(st.session_state.current_questions, pd.DataFrame):
        df = load_data_smart(MBTI_URL, "MBTI")
        if df is None: st.stop()
        if st.session_state.mbti_mode == "Explore":
            dims = ['E / I', 'S / N', 'T / F', 'J / P']
            qs = draw_questions(df, 'Dimension', dims, 5)
        else: qs = df
        st.session_state.current_questions = qs
    
    qs = st.session_state.current_questions
    idx = len(st.session_state.mbti_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        c1, c2 = st.columns(2)
        if c1.button(str(row['Option_A']), key=f"ma{idx}"): st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
        if c2.button(str(row['Option_B']), key=f"mb{idx}"): st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
    else:
        res_df = pd.DataFrame(st.session_state.mbti_answers)
        final_mbti = ""
        if not res_df.empty and 'dim' in res_df.columns:
            for d in ['E / I', 'S / N', 'T / F', 'J / P']:
                sub = res_df[res_df['dim'] == d]
                a_count = (sub['score']=='A').sum(); b_count = (sub['score']=='B').sum()
                final_mbti += d[0] if a_count >= b_count else d[4]
        st.session_state.mbti_res = final_mbti
        st.session_state.step = "chakra_pre"
        st.session_state.current_questions = []
        st.rerun()

# 頁面 D: 脈輪前導
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI 分析結果: {st.session_state.mbti_res}")
    c1, c2 = st.columns(2)
    if c1.button("⚡ 快速檢測"): 
        st.session_state.chakra_mode = "Quick"
        st.session_state.current_questions = []
        st.session_state.step = "chakra_quiz"; st.rerun()
    if c2.button("🔮 深度檢測"): 
        st.session_state.chakra_mode = "Deep"
        st.session_state.current_questions = []
        st.session_state.step = "chakra_quiz"; st.rerun()

# 頁面 E: 脈輪測驗
elif st.session_state.step == "chakra_quiz":
    if not isinstance(st.session_state.current_questions, pd.DataFrame):
        df_c = load_data_smart(CHAKRA_URL, "Chakra")
        if df_c is None: st.stop()
        chakras = ["海底輪", "臍輪", "太陽輪", "心輪", "喉輪", "眉心輪", "頂輪"]
        count = 4 if st.session_state.chakra_mode == "Quick" else 8
        qs = draw_questions(df_c, 'Chakra_Category', chakras, count)
        st.session_state.current_questions = qs
        
    qs = st.session_state.current_questions
    idx = len(st.session_state.chakra_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        val = st.slider("符合程度 (1-5)", 1, 5, 3, key=f"c{idx}")
        if st.button("下一題"):
            st.session_state.chakra_answers[idx] = {'cat': row['Chakra_Category'], 'val': val}; st.rerun()
    else:
        res_df = pd.DataFrame(st.session_state.chakra_answers).T
        st.session_state.chakra_res = res_df.groupby('cat')['val'].mean().to_dict()
        st.session_state.step = "result"; st.rerun()

# 頁面 F: 結果報告
elif st.session_state.step == "result":
    df_logic = load_data_smart(LOGIC_URL, "Logic")
    df_prod = load_data_smart(PRODUCT_URL, "Product")
    
    scores = st.session_state.chakra_res
    user_mbti = st.session_state.mbti_res
    
    st.title("🔮 全方位能量診斷報告")
    st.markdown(f"**MBTI 類型：{user_mbti}**")
    
    # 排序與分數換算
    ordered_chakras = ["海底輪", "臍輪", "太陽輪", "心輪", "喉輪", "眉心輪", "頂輪"]
    final_scores = {k: scores.get(k, 0) for k in ordered_chakras}
    converted_scores = {k: (v - 1) * 25 for k, v in final_scores.items()}
    
    # 【優化 1】雷達圖顯示數字 (text=r)
    df_plot = pd.DataFrame(dict(r=list(converted_scores.values()), theta=list(converted_scores.keys())))
    fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, text='r', color_discrete_sequence=['#d4af37'])
    fig.update_polars(radialaxis=dict(range=[0, 100], showticklabels=False)) # 隱藏軸線標籤，只看數據點
    fig.update_traces(textposition='top center') # 數字顯示在點上方
    st.plotly_chart(fig)
    
    st.divider()
    st.subheader("📊 脈輪能量深度解析")
    
    # 邏輯判定函數
    def get_status_from_logic(score_100):
        if score_100 <= 35: return "Weak"
        elif score_100 <= 60: return "Blocked"
        elif score_100 <= 85: return "Balanced"
        else: return "Excellent"
    
    for chakra in ordered_chakras:
        score_100 = converted_scores[chakra]
        status_key = get_status_from_logic(score_100)
        desc = "暫無說明"; advice = ""
        
        # 【優化 2】修復 KeyError：只依賴 Status 欄位進行比對 (通用邏輯表)
        if df_logic is not None:
            # 確保欄位存在
            if "Status" in df_logic.columns:
                match = df_logic[df_logic['Status'].astype(str).str.contains(status_key, case=False, na=False)]
                if not match.empty:
                    desc = match.iloc[0].get('Description', desc)
                    advice = match.iloc[0].get('Advice', '')

        with st.expander(f"{chakra} (能量指數: {score_100:.0f})"):
            st.markdown(f"**狀態：** {status_key} ({desc})")
            if advice: st.markdown(f"**建議：** {advice}")

    st.divider()
    st.subheader("💎 您的命定能量水晶")
    
    target_chakra = min(converted_scores, key=converted_scores.get)
    st.info(f"偵測到您的 **{target_chakra}** 最需要支持，專屬推薦：")
    
    rec_product = None
    if df_prod is not None:
        c_match = df_prod[df_prod['Chakra_Category'].str.contains(target_chakra, case=False, na=False)]
        m_match = c_match[c_match['MBTI_Match'].astype(str).str.contains(user_mbti, case=False, na=False)]
        
        if not m_match.empty: rec_product = m_match.iloc[0]
        elif not c_match.empty: rec_product = c_match.iloc[0]
    
    if rec_product is not None:
        st.markdown(f"""
        <div class="report-card">
            <h3>👑 {rec_product['Product_Name']}</h3>
            <p><strong>🔮 首選晶石：</strong> {rec_product.get('Preferred_Gemstones', '依設計師搭配')}</p>
            <p>專為 <strong>{target_chakra}</strong> 與 <strong>{user_mbti}</strong> 打造。</p>
        </div>
        """, unsafe_allow_html=True)
        
        link = rec_product.get('Store_Link', 'https://www.instagram.com/tinting12o3/')
        if pd.isna(link) or str(link).strip() == "": link = "https://www.instagram.com/tinting12o3/"
        
        st.link_button(f"來這瞧瞧 👀 ({rec_product['Product_Name']})", link, type="primary")
    else:
        st.warning("暫無匹配產品")
        st.link_button("來這瞧瞧 👀 (私訊諮詢)", "https://ig.me/m/tinting12o3/")

    if st.button("🔄 重新測驗"):
        st.session_state.clear(); st.rerun()
