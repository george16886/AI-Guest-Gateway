import streamlit as st
import httpx
import time
import pandas as pd

# FastAPI Backend URL
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Host Dashboard - Local AI Guest Gateway",
    page_icon="🤖",
    layout="wide"
)

st.title("Local AI Guest Gateway - Host Dashboard")
st.markdown("審核區域網路內訪客的 Ollama AI 算力使用申請。")

# Auto-refresh using st.rerun() (Refresh every 5 seconds)
# We can use a simple sleep and rerun for auto-refresh, or manual refresh button
col1, col2 = st.columns([8, 2])
with col1:
    st.subheader("待審核申請 (Pending Requests)")
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

# Auto refresh trick (every 5 seconds)
time.sleep(5)
st.rerun()
