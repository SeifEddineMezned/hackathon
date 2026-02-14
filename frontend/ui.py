import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Config
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI MINDS", layout="wide")

st.title("🧠 AI MINDS Cognitive Assistant")

# Sidebar
st.sidebar.header("System Status")
try:
    status = requests.get(f"{API_URL}/status", timeout=2).json()
    st.sidebar.success(f"Backend: {status['status']}")
    st.sidebar.info(f"Watcher: {'Active' if status['watcher'] else 'Inactive'}")
except:
    st.sidebar.error("Backend Offline")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat & Query", "📅 Memory Timeline", "✅ Action Items"])

with tab1:
    st.header("Ask your Memory")
    query = st.text_input("What would you like to know?", placeholder="What did I decide about the project deadline?")
    
    if st.button("Ask AI"):
        if not query:
            st.warning("Please enter a query.")
        else:
            with st.spinner("Reasoning..."):
                try:
                    res = requests.post(f"{API_URL}/query", json={"query": query}).json()
                    
                    st.markdown(f"### Answer")
                    st.write(res["answer"])
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Confidence", f"{res['confidence']}%")
                    col2.markdown(f"**Intent:** {res['intent']}")
                    
                    if res["citations"]:
                        with st.expander("Evidence Sources"):
                            for cid in res["citations"]:
                                st.text(f"Event ID: {cid}")
                                
                    if res["uncertainty_flags"]:
                        st.error(f"Flags: {', '.join(res['uncertainty_flags'])}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.header("Recent Memories")
    if st.button("Refresh Timeline"):
        st.experimental_rerun()
        
    try:
        events = requests.get(f"{API_URL}/timeline").json()
        if events:
            df = pd.DataFrame(events)
            df['created_at'] = pd.to_datetime(df['created_at'])
            st.dataframe(df[['created_at', 'source_type', 'summary', 'topics']], use_container_width=True)
            
            for evt in events[:5]:
                with st.expander(f"{evt['created_at']} - {evt['summary']}"):
                    st.write(f"Source: {evt['source_type']}")
                    st.write(f"Topics: {evt['topics']}")
                    st.write(f"ID: {evt['id']}")
        else:
            st.info("No memories yet.")
    except:
        st.warning("Could not fetch timeline.")

with tab3:
    st.header("Action Items")
    filter_status = st.radio("Filter", ["All", "open", "done"], horizontal=True)
    
    params = {}
    if filter_status != "All":
        params["status"] = filter_status
        
    try:
        actions = requests.get(f"{API_URL}/actions", params=params).json()
        if actions:
            for action in actions:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.markdown(f"**{action['task']}**")
                col2.caption(f"Due: {action['due_date'] or 'None'}")
                col3.caption(f"Priority: {action['priority']}")
                st.divider()
        else:
            st.info("No action items found.")
            
    except:
        st.warning("Could not fetch actions.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Inbox Monitor")
st.sidebar.code("./inbox/\n  /text\n  /docs\n  /images\n  /audio")
