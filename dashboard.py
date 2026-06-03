import streamlit as st
import httpx
import time
import pandas as pd
from datetime import datetime

# FastAPI Backend URL
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Host Dashboard - Local AI Guest Gateway",
    page_icon="🤖",
    layout="wide"
)

st.title("Local AI Guest Gateway - Host Dashboard")
st.markdown("審核區域網路內訪客的 Ollama AI 算力使用申請與監控狀態。")

# Create Tabs
tab1, tab2 = st.tabs(["📋 待審核申請 (Pending)", "📊 數據分析戰情室 (Analytics)"])

with tab1:
    col1, col2 = st.columns([8, 2])
    with col1:
        st.subheader("待審核申請")
    with col2:
        if st.button("🔄 手動刷新 (Refresh)"):
            st.rerun()

    try:
        response = httpx.get(f"{API_BASE_URL}/admin/pending", timeout=5.0)
        response.raise_for_status()
        pending_requests = response.json()
    except Exception as e:
        st.error(f"無法連線至 FastAPI 後端 ({API_BASE_URL}): {e}")
        st.stop()

    if not pending_requests:
        st.info("目前沒有任何待審核的訪客申請。")
    else:
        for req in pending_requests:
            with st.container():
                st.markdown(f"### 訪客: **{req['guest_name']}**")
                st.text(f"Session ID: {req['session_id']}")
                st.text(f"申請時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(req['created_at']))}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ 同意 (Approve)", key=f"approve_{req['session_id']}"):
                        try:
                            res = httpx.post(f"{API_BASE_URL}/admin/approve/{req['session_id']}")
                            res.raise_for_status()
                            st.success(f"已核准 {req['guest_name']} 的申請！")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"核准失敗: {e}")
                with col_b:
                    if st.button("❌ 拒絕 (Reject)", key=f"reject_{req['session_id']}"):
                        try:
                            res = httpx.post(f"{API_BASE_URL}/admin/reject/{req['session_id']}")
                            res.raise_for_status()
                            st.warning(f"已拒絕 {req['guest_name']} 的申請。")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"拒絕失敗: {e}")
            st.divider()

with tab2:
    st.subheader("伺服器算力消耗統計")
    if st.button("🔄 刷新數據", key="refresh_analytics"):
        st.rerun()
        
    try:
        analytics_response = httpx.get(f"{API_BASE_URL}/admin/analytics", timeout=5.0)
        if analytics_response.status_code == 200:
            data = analytics_response.json()
            
            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("總消耗 Tokens", f"{data['total_tokens']:,}")
            m2.metric("總申請次數", data['total_requests'])
            m3.metric("已核准", data['approved'])
            m4.metric("已拒絕", data['rejected'])
            
            st.divider()
            
            # Chart and Table
            sessions = data.get('sessions', [])
            if sessions:
                df = pd.DataFrame(sessions)
                df['created_at'] = pd.to_datetime(df['created_at'], unit='s')
                
                col_chart, col_table = st.columns([1, 1])
                
                with col_chart:
                    st.markdown("#### 訪客 Token 消耗排行榜")
                    # Filter approved or token used > 0
                    usage_df = df[df['token_used'] > 0][['guest_name', 'token_used']].sort_values('token_used', ascending=False)
                    if not usage_df.empty:
                        st.bar_chart(data=usage_df, x='guest_name', y='token_used', use_container_width=True)
                    else:
                        st.info("尚無 Token 消耗數據。")
                        
                with col_table:
                    st.markdown("#### 所有紀錄")
                    display_df = df[['guest_name', 'status', 'token_used', 'created_at']].sort_values('created_at', ascending=False)
                    st.dataframe(display_df, use_container_width=True)
            else:
                st.info("目前沒有任何紀錄。")
    except Exception as e:
        st.error(f"無法取得統計數據: {e}")

# Auto refresh trick (every 5 seconds)
# Note: Streamlit reruns the whole script. In a real app with tabs, auto-rerun might reset tab state.
# We will use st.empty() or just simple time.sleep()
time.sleep(5)
st.rerun()
