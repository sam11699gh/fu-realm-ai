import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. 基礎配置 ---
st.set_page_config(page_title="Fù Realm 能量顧問", page_icon="✨", layout="centered")

# 品牌金色視覺
st.markdown("""
    <style>
    .main { background-color: #fcfaf2; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #d4af37; background-color: white; color: #d4af37; font-weight: bold; height: 3em; }
    .stButton>button:hover { background-color: #d4af37; color: white; }
    .stProgress > div > div > div > div { background-color: #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化 Session State (記憶體) ---
if "step" not in st.session_state:
    st.session_state.step = "welcome"
    st.session_state.mbti_answers = []
    st.session_state.chakra_answers = {}
    st.session_state.mbti_res = ""
    st.session_state.chakra_res = {}

# --- 3. 側邊欄：連結設定 ---
with st.sidebar:
    st.title("🛡️ 系統核心設定")
    api_key = st.text_input("Gemini API Key", type="password")
    st.info("💡 請貼上各分頁發布為 CSV 的連結")
    mbti_q_url = st.text_input("MBTI 題庫連結 (分頁5)")
    chakra_q_url = st.text_input("脈輪題庫連結 (分頁1)")
    
    if st.button("🔄 重置所有進度"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- 4. 核心邏輯函數 ---
@st.cache_data
def load_data(url):
    try: return pd.read_csv(url)
    except: return None

def calc_mbti(ans_list):
    # ans_list 格式: [{'dim': 'E/I', 'score': 'A'}, ...]
    df = pd.DataFrame(ans_list)
    res = ""
    for d in ['E / I', 'S / N', 'T / F', 'J / P']:
        sub = df[df['dim'] == d]
        a_count = (sub['score'] == 'A').sum()
        b_count = (sub['score'] == 'B').sum()
        res += d[0] if a_count >= b_count else d[4]
    return res

# --- 5. 測驗流程 ---

# A. 歡迎與模式選擇
if st.session_state.step == "welcome":
    st.title("✨ Fù Realm 能量診斷系統")
    st.write("請選擇 MBTI 探索模式：")
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 已知型\n(直接輸入)"): 
        st.session_state.mbti_mode = "Known"; st.session_state.step = "mbti_input"
        st.rerun()
    if c2.button("🔍 探索型\n(20題)"): 
        st.session_state.mbti_mode = "Explore"; st.session_state.step = "mbti_quiz"
        st.rerun()
    if c3.button("💎 深層型\n(60題)"): 
        st.session_state.mbti_mode = "Deep"; st.session_state.step = "mbti_quiz"
        st.rerun()

# B. MBTI 輸入/測驗
elif st.session_state.step == "mbti_input":
    m = st.selectbox("您的 MBTI 是？", ["INTJ","INFP","ENFJ","ENTP","ISTJ","ISFP","ESTP","ESFJ","INFJ","ENTJ","INTP","ENFP","ISTP","ISFJ","ESTJ","ESFP"])
    if st.button("下一步：脈輪檢測"):
        st.session_state.mbti_res = m; st.session_state.step = "chakra_pre"
        st.rerun()

elif st.session_state.step == "mbti_quiz":
    df_m = load_data(mbti_q_url)
    if df_m is not None:
        qs = df_m if st.session_state.mbti_mode == "Deep" else df_m[df_m['Mode'].str.contains("探索")]
        idx = len(st.session_state.mbti_answers)
        
        if idx < len(qs):
            row = qs.iloc[idx]
            st.subheader(f"MBTI 測驗 ({idx+1}/{len(qs)})")
            st.progress((idx+1)/len(qs))
            st.write(row['Question'])
            if st.button(row['Option_A'], key=f"ma{idx}"):
                st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'A'})
                st.rerun()
            if st.button(row['Option_B'], key=f"mb{idx}"):
                st.session_state.mbti_answers.append({'dim': row['Dimension'], 'score': 'B'})
                st.rerun()
        else:
            st.session_state.mbti_res = calc_mbti(st.session_state.mbti_answers)
            st.session_state.step = "chakra_pre"
            st.rerun()

# C. 脈輪測驗模式選擇
elif st.session_state.step == "chakra_pre":
    st.success(f"MBTI 分析完成：{st.session_state.mbti_res}")
    st.subheader("選擇脈輪檢測深度")
    col1, col2 = st.columns(2)
    if col1.button("⚡ 快速檢測 (14題)"):
        st.session_state.chakra_mode = "Quick"; st.session_state.step = "chakra_quiz"
        st.rerun()
    if col2.button("🔮 深度掃描 (56題)"):
        st.session_state.chakra_mode = "Deep"; st.session_state.step = "chakra_quiz"
        st.rerun()

elif st.session_state.step == "chakra_quiz":
    df_c = load_data(chakra_q_url)
    if df_c is not None:
        qs = df_c[df_c['Mode'].str.contains("快速")] if st.session_state.chakra_mode == "Quick" else df_c
        idx = len(st.session_state.chakra_answers)
        
        if idx < len(qs):
            row = qs.iloc[idx]
            st.subheader(f"脈輪掃描 ({idx+1}/{len(qs)})")
            st.progress((idx+1)/len(qs))
            st.write(row['Question'])
            score = st.slider("符合程度", 1, 5, 3, key=f"cs{idx}")
            if st.button("下一題", key=f"cb{idx}"):
                chakra_name = row['Chakra_Category']
                st.session_state.chakra_answers[idx] = {'cat': chakra_name, 'val': score}
                st.rerun()
        else:
            # 計算分數 (轉換為 0-100)
            final_df = pd.DataFrame(st.session_state.chakra_answers).T
            st.session_state.chakra_res = final_df.groupby('cat')['val'].mean().to_dict()
            st.session_state.step = "result"
            st.rerun()

# D. 結果與 AI 報告
elif st.session_state.step == "result":
    st.title("🔮 您的能量診斷報告")
    
    # 雷達圖
    df_plot = pd.DataFrame(dict(r=list(st.session_state.chakra_res.values()), theta=list(st.session_state.chakra_res.keys())))
    fig = px.line_polar(df_plot, r='r', theta='theta', line_close=True, color_discrete_sequence=['#d4af37'])
    fig.update_polars(radialaxis_range=[1, 5])
    st.plotly_chart(fig)
    
    if st.button("✨ 召喚 AI 生成深度處方"):
        with st.spinner("AI 正在感應您的能量頻率..."):
            genai.configure(api_key=api_key)
            prompt = f"我是{st.session_state.mbti_res}, 脈輪平均分(1-5)如下:{st.session_state.chakra_res}。請以Fù Realm水晶專家的語氣,根據Scoring_Logic提供簡短分析、肯定語及推薦晶石。最後引導用戶私訊截圖領優惠。"
            response = genai.GenerativeModel('gemini-1.5-pro').generate_content(prompt)
            st.markdown(response.text)
            st.divider()
            st.link_button("📩 私訊專業顧問 (領取專屬優惠)", "https://ig.me/m/tinting12o3/")

    if st.button("🔄 重新測驗"):
        st.session_state.step = "welcome"; st.rerun()
