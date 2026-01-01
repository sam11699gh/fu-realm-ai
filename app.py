import streamlit as st
import pandas as pd
import plotly.express as px

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

# --- 2. 萬能讀取器 (強化版) ---
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
            
            # 基本題庫
            if any(x in c for x in ["題目", "問題", "question", "content"]): rename_map[col] = "Question"
            elif any(x in c for x in ["模式", "type", "mode"]): rename_map[col] = "Mode"
            elif any(x in c for x in ["維度", "dim"]): rename_map[col] = "Dimension"
            elif "optiona" in c or "選項a" in c: rename_map[col] = "Option_A"
            elif "optionb" in c or "選項b" in c: rename_map[col] = "Option_B"
            elif any(x in c for x in ["分類", "脈輪", "category", "chakra", "focus"]): rename_map[col] = "Chakra_Category"
            
            # 產品表 (Products.csv)
            elif "product" in c or "商品" in c: rename_map[col] = "Product_Name"
            elif "gem" in c or "晶石" in c or "stone" in c: rename_map[col] = "Preferred_Gemstones"
            elif "link" in c or "連結" in c or "url" in c: rename_map[col] = "Store_Link"
            elif "mbti" in c and "match" in c: rename_map[col] = "MBTI_Match"
            
            # 邏輯表 (Scoring_Logic.csv)
            elif "status" in c or "狀態" in c or "range" in c or "score" in c: rename_map[col] = "Status" # 例如 Low, High
            elif "desc" in c or "說明" in c or "explanation" in c: rename_map[col] = "Description"
            elif "advice" in c or "建議" in c: rename_map[col] = "Advice"

        df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        return None

# --- 3. 輔助樣式 ---
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    .report-card { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #d4af37; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 狀態管理 ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = "INFJ" # 預設值，避免除錯時報錯
    st.session_state.chakra_res = {}

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
    if df is not None and "Option_A" not in df.columns: st.error("MBTI 題庫錯誤"); st.stop()

    qs = df if st.session_state.mbti_mode == "Deep" else df[df['Mode'].astype(str).str.contains("探索", na=False)]
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
    if df_c is not None and "Chakra_Category" not in df_c.columns: st.error("脈輪題庫錯誤"); st.stop()
    
    qs = df_c[df_c['Mode'].astype(str).str.contains("快速", na=False)] if st.session_state.chakra_mode == "Quick" else df_c
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

# 頁面 F: 結果報告 (精準導購版)
elif st.session_state.step == "result":
    # 載入邏輯與產品表
    df_logic = load_data_smart(LOGIC_URL, "Logic")
    df_prod = load_data_smart(PRODUCT_URL, "Product")
    
    scores = st.session_state.chakra_res
    user_mbti = st.session_state.mbti_res
    
    st.title("🔮 全方位能量診斷報告")
    st.markdown(f"**MBTI 類型：{user_mbti}**")
    
    # 1. 雷達圖
    if scores:
        df_plot = pd.DataFrame(dict(r=list(scores.values()), theta=list(scores.keys())))
        fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
        fig.update_polars(radialaxis_range=[0, 5])
        st.plotly_chart(fig)
        
        st.divider()
        
        # 2. 七大脈輪詳細說明 (Scoring_Logic)
        st.subheader("📊 脈輪能量深度解析")
        
        # 定義狀態判定 (可依據您的 CSV 邏輯調整)
        def get_status(score):
            if score < 2.5: return "Low" # 或 "弱"
            elif score > 4.0: return "High" # 或 "強"
            else: return "Balanced" # 或 "平衡"
            
        for chakra, score in scores.items():
            status = get_status(score)
            desc = "暫無說明"
            
            # 從 Logic 表找對應說明
            if df_logic is not None:
                # 模糊比對脈輪名稱與狀態
                match = df_logic[
                    (df_logic['Chakra_Category'].str.contains(chakra, case=False, na=False)) &
                    (df_logic['Status'].str.contains(status, case=False, na=False))
                ]
                if not match.empty:
                    desc = match.iloc[0]['Description']
            
            with st.expander(f"{chakra} (指數: {score:.1f} - {status})"):
                st.write(desc)

        st.divider()

        # 3. 專屬商品推薦 (Product Match)
        st.subheader("💎 您的命定能量水晶")
        
        # 找出最弱的脈輪 (Focus)
        target_chakra = min(scores, key=scores.get)
        st.info(f"偵測到您的 **{target_chakra}** 能量最需要支持，結合您的 **{user_mbti}** 特質，我們為您挑選：")
        
        rec_product = None
        
        if df_prod is not None:
            # 第一層：篩選脈輪
            chakra_matches = df_prod[df_prod['Chakra_Category'].str.contains(target_chakra, case=False, na=False)]
            
            # 第二層：篩選 MBTI
            # 檢查 MBTI_Match 欄位是否包含使用者的 MBTI (例如 "INFJ, INFP" 字串包含 "INFJ")
            mbti_matches = chakra_matches[chakra_matches['MBTI_Match'].astype(str).str.contains(user_mbti, case=False, na=False)]
            
            if not mbti_matches.empty:
                rec_product = mbti_matches.iloc[0] # 取最符合的第一個
            elif not chakra_matches.empty:
                rec_product = chakra_matches.iloc[0] # 如果沒對到 MBTI，至少對到脈輪
        
        # 4. 顯示推薦結果
        if rec_product is not None:
            # 顯示卡片
            st.markdown(f"""
            <div class="report-card">
                <h3>👑 {rec_product['Product_Name']}</h3>
                <p><strong>🔮 首選晶石：</strong> {rec_product.get('Preferred_Gemstones', '依設計師搭配')}</p>
                <p>這款水晶專為 <strong>{target_chakra}</strong> 設計，特別適合 <strong>{user_mbti}</strong> 的您，能有效轉化當下的能量場。</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 導購按鈕
            link = rec_product.get('Store_Link', 'https://www.instagram.com/tinting12o3/')
            # 如果 CSV 裡沒填連結，或是 NaN，就用預設 IG
            if pd.isna(link) or str(link).strip() == "":
                link = "https://www.instagram.com/tinting12o3/"
                
            st.link_button(f"👉 點此前往購買 ({rec_product['Product_Name']})", link, type="primary")
            
        else:
            # 萬一 CSV 讀不到或沒對到
            st.warning("目前資料庫中暫無完全匹配的組合，建議私訊諮詢師。")
            st.link_button("📩 私訊人工諮詢", "https://ig.me/m/tinting12o3/")

    if st.button("🔄 重新測驗"):
        st.session_state.clear(); st.rerun()
