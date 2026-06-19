import os
import sys
import subprocess
import pandas as pd
import streamlit as st
from datetime import datetime
from glob import glob
from streamlit_autorefresh import st_autorefresh
from streamlit_option_menu import option_menu

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from settings.config import load_settings
from storage.csv_storage import read_collector_status, get_csv_path, read_today_trades
from dashboard.styles import get_custom_css, get_tv_mode_css
from dashboard.views import (
    render_summary_cards,
    render_settings_page,
    render_tv_mode,
    render_alert_banner,
    render_live_dashboard,
    render_about_page,
    render_hot_bulk_stocks_page,
    render_largest_trades_page,
    render_symbol_analytics_page,
    render_live_alerts_page,
    render_bulk_history_page
)

# Check and initialize TV Mode session state
query_params = st.query_params
if "page" in query_params and query_params["page"] == "tv":
    st.session_state.tv_mode = True

is_tv_mode = st.session_state.get("tv_mode", False)
sidebar_state = "collapsed" if is_tv_mode else "expanded"

# 1. Page Config
st.set_page_config(
    page_title="NEPSE Live Bulk Market Analyzer",
    layout="wide",
    initial_sidebar_state=sidebar_state
)

# Load current settings
settings = load_settings()
data_folder = settings.get("data_folder", "data")
refresh_interval = st.session_state.get("refresh_interval", settings.get("refresh_interval", 15))
bulk_threshold = settings.get("bulk_threshold", 5000)
auto_start = settings.get("auto_start_collector", True)
enable_sound = settings.get("enable_sound", True)

# 2. Check and Auto-Start Collector Process
status_data = read_collector_status(data_folder)
c_status = status_data.get("status", "offline")
last_heartbeat = status_data.get("last_heartbeat")

# Heartbeat verification
is_collector_alive = False
if last_heartbeat:
    try:
        hb_time = datetime.fromisoformat(last_heartbeat)
        time_diff = (datetime.now() - hb_time).total_seconds()
        if time_diff < 40: # If updated in last 40 seconds, it's alive
            is_collector_alive = True
    except Exception:
        pass

if not is_collector_alive:
    c_status = "offline"

# Spin up collector daemon if offline and auto_start is enabled
if c_status == "offline" and auto_start:
    st.info("Starting background NEPSE Collector process...")
    try:
        collector_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "collector.py"))
        
        # On Windows, we launch it with CREATE_NEW_CONSOLE so the user has a visible terminal console
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, collector_script],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True
            )
        else:
            # Unix/Mac background process launch
            subprocess.Popen(
                [sys.executable, collector_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        st.toast("Background collector process started successfully!", icon="🚀")
        # Give it a second to start and write status
        import time
        time.sleep(1.5)
        # Reload status
        status_data = read_collector_status(data_folder)
        c_status = status_data.get("status", "offline")
    except Exception as e:
        st.error(f"Failed to auto-start collector process: {e}")

# 3. Read Today's Data
active_business_date = status_data.get("business_date")

# If collector hasn't run yet or date is None, check files in folder
if not active_business_date or active_business_date == "N/A":
    csv_files = glob(os.path.join(data_folder, "*.csv"))
    if csv_files:
        # Get most recent CSV based on file name/date sorting
        csv_files.sort()
        newest_file = csv_files[-1]
        active_business_date = os.path.basename(newest_file).replace(".csv", "")
    else:
        active_business_date = datetime.now().strftime("%Y-%m-%d")

csv_path = get_csv_path(active_business_date, data_folder)
trades_df = read_today_trades(csv_path)

# 4. Navigation & Sidebar Layout
page = "Live Bulk"

is_tv_mode = st.session_state.get("tv_mode", False)

if is_tv_mode:
    page = "TV Mode"
else:
    # Standard Sidebar navigation
    with st.sidebar:
        # Title and logo matching user mockup
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px; padding: 10px 0 0 10px;">
                <div style="font-size: 28px; color: #a78bfa; filter: drop-shadow(0 0 8px #8b5cf6);">📈</div>
                <div>
                    <h2 style="margin: 0; font-size: 20px; font-weight: 900; letter-spacing: 0.5px; color: white;">NEPSE</h2>
                    <span style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">Live Bulk Analyzer</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Option Menu sidebar list matching the mockup layout and purple color scheme
        page = option_menu(
            menu_title=None,
            options=["Live Bulk", "🔥 Hot Bulk Stocks", "💰 Largest Trades", "📊 Symbol Analytics", "⚡ Live Alerts", "📋 Bulk Trade History", "Settings", "About"],
            icons=["broadcast", "fire", "cash-coin", "graph-up", "bell-fill", "journal-text", "sliders", "info-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"background-color": "#0b0f19", "padding": "0px"},
                "icon": {"color": "#94a3b8", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin": "4px 8px", 
                    "color": "#94a3b8", 
                    "font-family": "Inter",
                    "font-weight": "500",
                    "border-radius": "8px"
                },
                "nav-link-selected": {"background-color": "#581c87", "color": "#ffffff", "font-weight": "700"},
            }
        )
        
        st.markdown("---")
        
        # Sidebar Status Panel
        st.markdown("### 📡 Collector Node")
        if c_status == "offline":
            st.markdown('Status: <span class="status-dot offline"></span> **Offline**', unsafe_allow_html=True)
            if st.button("Start Collector Daemon"):
                try:
                    collector_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "collector.py"))
                    if sys.platform == "win32":
                        subprocess.Popen([sys.executable, collector_script], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    else:
                        subprocess.Popen([sys.executable, collector_script], start_new_session=True)
                    st.success("Collector started!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        elif c_status in ("checking", "live_sync", "running"):
            st.markdown('Status: <span class="status-dot online"></span> **Online (Active)**', unsafe_allow_html=True)
        else: # historical sync / syncing
            progress = status_data.get("sync_progress", "")
            st.markdown(f'Status: <span class="status-dot syncing"></span> **Syncing**<br><small>{progress}</small>', unsafe_allow_html=True)
            
        st.markdown(f"**Business Date**: `{active_business_date}`")
        st.markdown(f"**Captured Trades**: `{len(trades_df):,}`")
        
        # Market open indicator matching user mockup
        st.markdown("---")
        st.markdown(
            """
            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 20px; padding: 6px 14px; display: inline-flex; align-items: center; gap: 8px;">
                <span style="color: #10b981; font-weight: bold; font-size: 10px;">●</span>
                <span style="color: #10b981; font-weight: bold; font-size: 12px; font-family: 'Inter', sans-serif;">NEPSE Market is Open</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# 5. Inject Styles & Render Page
if page == "TV Mode":
    st.markdown(get_tv_mode_css(), unsafe_allow_html=True)
    # Enable auto-refresh on TV mode
    st_autorefresh(interval=1000 * refresh_interval, key="tv_refresh_timer")
    render_tv_mode(trades_df, bulk_threshold, refresh_interval, enable_sound)
else:
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    if page == "Live Bulk":
        # Enable auto-refresh
        st_autorefresh(interval=1000 * refresh_interval, key="dashboard_refresh_timer")
        
        # Top Header layout with audited color schemas and Key Metrics toggles
        col_title, col_clock, col_toggle, col_tv = st.columns([5.5, 2.5, 2, 2])
        with col_title:
            st.markdown("""
            <h1 style="margin: 0; padding: 0; font-size: 32px; font-weight: 900; font-family: 'Outfit'; color: white; background: none; -webkit-text-fill-color: initial;">NEPSE Live Bulk Market Analyzer</h1>
            <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 14px; font-family: 'Inter'; font-weight: 500;">
                Real-time Bulk Trade Monitoring & Market Intelligence &nbsp;<span style="color: #22C55E; font-weight: bold;">• LIVE</span>
            </p>
            """, unsafe_allow_html=True)

        with col_clock:
            now_str = datetime.now().strftime("%I:%M:%S %p")
            date_str = datetime.now().strftime("%a, %b %d, %Y")
            st.markdown(f"""
            <div style="background-color: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 8px 16px; display: flex; align-items: center; gap: 12px; justify-content: center; height: 100%;">
                <span style="font-size: 20px; color: #8B5CF6;">🕒</span>
                <div style="text-align: left;">
                    <div style="font-family: 'Roboto Mono', monospace; font-size: 15px; font-weight: 700; color: white; line-height: 1.2;">{now_str}</div>
                    <div style="font-size: 11px; color: #94A3B8; line-height: 1.2; font-family: 'Inter'; font-weight: 500;">{date_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_toggle:
            st.write("")
            if "show_metrics" not in st.session_state:
                st.session_state.show_metrics = True
            metrics_label = "📊 HIDE METRICS" if st.session_state.show_metrics else "📊 SHOW METRICS"
            if st.button(metrics_label, type="secondary", use_container_width=True):
                st.session_state.show_metrics = not st.session_state.show_metrics
                st.rerun()

        with col_tv:
            st.write("") 
            if st.button("📺 TV MODE", type="primary", use_container_width=True):
                st.session_state.tv_mode = True
                st.rerun()
                
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # Render the full dashboard layout (filters, cards, panels, table, side activity panel)
        render_live_dashboard(trades_df, bulk_threshold, enable_sound)
        
    elif page == "🔥 Hot Bulk Stocks":
        st_autorefresh(interval=1000 * refresh_interval, key="hot_stocks_refresh_timer")
        render_hot_bulk_stocks_page(trades_df, bulk_threshold)
        
    elif page == "💰 Largest Trades":
        st_autorefresh(interval=1000 * refresh_interval, key="largest_trades_refresh_timer")
        render_largest_trades_page(trades_df, bulk_threshold)
        
    elif page == "📊 Symbol Analytics":
        render_symbol_analytics_page(trades_df, bulk_threshold)
        
    elif page == "⚡ Live Alerts":
        st_autorefresh(interval=1000 * refresh_interval, key="live_alerts_refresh_timer")
        render_live_alerts_page(trades_df, bulk_threshold)
        
    elif page == "📋 Bulk Trade History":
        render_bulk_history_page(trades_df, bulk_threshold)
        
    elif page == "Settings":
        render_settings_page(settings)
        
    elif page == "About":
        render_about_page()
