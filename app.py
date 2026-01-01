import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. 系統配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 讀取網址
try:
    MBTI_URL = st.secrets["MBTI_CSV_URL"]
    CHAKRA_URL = st.secrets["CHAKRA_CSV_URL"]
    # 預留產品與邏輯表連結 (若無可留空)
    PRODUCT_URL = st.secrets.get("PRODUCT_CSV_URL", "") 
    LOGIC_URL = st.secrets.get("LOGIC_CSV_URL", "")
except:
    st.error("⚠️ 系統設定讀取失敗，請檢查 Streamlit Secrets。")
    st.stop()

# --- 2. 超強版萬能讀取器 (修復 KeyError) ---
@st.cache_data
def load_data_smart(url, type_name):
    if not url: return None
    try:
        # 嘗試讀取
        try: df = pd.read_csv(url, encoding='utf-8')
        except: df = pd.read_csv(url, encoding='utf-8-sig') 
        
        # 清理欄位名稱 (去空白、轉小寫)
        df.columns = df.columns.str.strip()
        
        # 建立更強大的對照表
        rename_map = {}
        for col in df.columns:
            c = col.lower().replace("_", "").replace(" ", "") # 把底線和空白都拿掉來比對，更準
            
            # 關鍵字比對
            if any(x in c for x in ["題目", "問題", "question", "content"]): rename_map[col] = "Question"
            elif any(x in c for x in ["模式", "type", "mode"]): rename_map[col] = "Mode"
            elif any(x in c for x in ["維度", "dim"]): rename_map[col] = "Dimension"
            
            # 這裡修復了 OptionA 抓不到的問題
            elif "optiona" in c or "選項a" in c or "ansa" in c: rename_map[col] = "Option_A"
            elif "optionb" in c or "選項b" in c or "ansb" in c: rename_map[col] = "Option_B"
            
            elif any(x in c for x in ["分類", "脈輪", "category", "chakra"]): rename_map[col] = "Chakra_Category"
            elif any(x in c for x in ["產品", "名稱", "product"]): rename_map[col] = "Product_Name"
            elif any(x in c for x in ["連結", "link", "url"]): rename_map[col] = "Link"
            elif any(x in c for x in ["圖片", "image", "img"]): rename_map[col] = "Image"
            elif any(x in c for x in ["建議", "advice", "desc"]): rename_map[col] = "Advice"
        
        df.rename(columns=rename_map, inplace=True)
        return df
    except Exception as e:
        st.error(f"讀取錯誤: {e}")
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

# --- 4. 狀態管理 ---
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
    st.info("透過數據，精準解讀您的靈魂頻率")
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型"): st.session_state.step = "mbti_input"; st.rerun()
    if c2.button("🔍 探索型"): st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"; st.rerun()
    if c3.button("💎 深層型"): st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"; st.rerun()

# 頁面 B: 已知型輸入
elif st.session_state.step == "mbti_input":
    m = st.selectbox("選擇您的 MBTI", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"; st.rerun()

# 頁面 C: MBTI 測驗 (這裡就是原本報錯的地方)
elif st.session_state.step == "mbti_quiz":
    df = load_data_smart(MBTI_URL, "MBTI")
    
    # 防呆檢查：如果還是抓不到欄位，直接顯示錯誤給使用者看，方便除錯
    if df is not None and "Option_A" not in df.columns:
        st.error("⚠️ 欄位對應失敗，請檢查 CSV 標題。")
        st.write("系統讀到的所有欄位:", list(df.columns))
        st.stop()

    qs = df if st.session_state.mbti_mode == "Deep" else df[df['Mode'].astype(str).str.contains("探索", na=False)]
    idx = len(st.session_state.mbti_answers)
    
    if idx < len(qs):
        row = qs.iloc[idx]
        st.progress((idx+1)/len(qs))
        st.subheader(f"Q{idx+1}: {row['Question']}")
        
        c1, c2 = st.columns(2)
        # 現在這裡一定能抓到 Option_A 了
        if c1.button(str(row['Option_A']), key=f"ma{idx}"): 
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'}); st.rerun()
        if c2.button(str(row['Option_B']), key=f"mb{idx}"): 
            st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'}); st.rerun()
    else:
        # 結算
        res_df = pd.DataFrame(st.session_state.mbti_answers)
        final_mbti = ""
        if not res_df.empty and 'dim' in res_df.columns:
            for d in ['E / I', 'S / N', 'T / F', 'J / P']:
                sub = res_df[res_df['dim'] == d]
                # 簡單多數決
                a_count = (sub['score']=='A').sum()
                b_count = (sub['score']=='B').sum()
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
    
    # 防呆檢查
    if df_c is not None and "Chakra_Category" not in df_c.columns:
        st.error("⚠️ 脈輪題庫欄位對應失敗。")
        st.write("系統讀到的欄位:", list(df_c.columns))
        st.stop()

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
        res_df = pd.DataFrame(st.session_state.chakra_answers).T
        st.session_state.chakra_res = res_df.groupby('cat')['val'].mean().to_dict()
        st.session_state.step = "result"; st.rerun()

# 頁面 F: 結果報告 (純規則版)
elif st.session_state.step == "result":
    st.title("🔮 您的靈魂能量報告")
    
    scores = st.session_state.chakra_res
    if scores:
        # 找出最弱脈輪
        target_chakra = min(scores, key=scores.get) 
        target_score = scores[target_chakra]
        
        # 雷達圖
        df_plot = pd.DataFrame(dict(r=list(scores.values()), theta=list(scores.keys())))
        fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
        fig.update_polars(radialaxis_range=[0, 5])
        st.plotly_chart(fig)
        
        st.divider()
        
        # 結果文字
        st.subheader(f"⚠️ 能量關注焦點：{target_chakra}")
        st.write(f"您的 {target_chakra} 能量指數為 **{target_score:.1f}**，建議加強此處的能量平衡。")
        
        # 產品推薦區 (如果未來有設定 Product CSV 才會顯示詳細內容，否則顯示通用訊息)
        st.info("💡 專屬能量處方")
        st.write(f"針對 **{target_chakra}**，我們推薦您使用 Fù Realm 的專屬水晶進行療癒。")
        
        st.link_button(f"📩 私訊領取 {target_chakra} 專屬優惠", "https://ig.me/m/tinting12o3/")
    
    else:
        st.error("無法計算分數，請重新測驗。")

    if st.button("🔄 重新測驗"):
        st.session_state.clear(); st.rerun()
