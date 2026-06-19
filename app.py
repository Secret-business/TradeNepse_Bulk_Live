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
    render_tv_mode,
    render_live_dashboard,
    render_hot_bulk_stocks_page,
    render_largest_trades_page,
    render_symbol_analytics_page,
    render_live_alerts_page,
    render_coming_soon_page
)

# Check and initialize TV Mode session state
query_params = st.query_params
if "page" in query_params and query_params["page"] == "tv":
    st.session_state.tv_mode = True

is_tv_mode = st.session_state.get("tv_mode", False)
sidebar_state = "collapsed" if is_tv_mode else "expanded"

# 1. Page Config
st.set_page_config(
    page_title="TradeNepse",
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
        # Give it a second to start and write status
        import time
        time.sleep(1.5)
        # Reload status
        status_data = read_collector_status(data_folder)
        c_status = status_data.get("status", "offline")
    except Exception as e:
        print(f"Failed to auto-start collector process: {e}")

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
page = "📊 Dashboard"

is_tv_mode = st.session_state.get("tv_mode", False)

if is_tv_mode:
    page = "TV Mode"
else:
    # Standard Sidebar navigation
    with st.sidebar:
        # Title and logo
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px; padding: 10px 0 0 10px;">
                <div style="font-size: 28px; color: #a78bfa; filter: drop-shadow(0 0 8px #8b5cf6);">📈</div>
                <div>
                    <h2 style="margin: 0; font-size: 20px; font-weight: 900; letter-spacing: 0.5px; color: white;">TradeNepse</h2>
                    <span style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">Market Intelligence</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Option Menu sidebar list
        page = option_menu(
            menu_title=None,
            options=[
                "📊 Dashboard", 
                "🔥 Hot Stocks", 
                "💰 Largest Trades", 
                "📈 Symbol Analytics", 
                "🚨 Live Alerts", 
                "🎯 Trade Planner (Coming Soon)", 
                "🤖 Market Scanner (Coming Soon)"
            ],
            icons=["grid", "fire", "cash-coin", "graph-up", "bell-fill", "compass", "robot"],
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

# 5. Inject Styles & Render Page
if page == "TV Mode":
    st.markdown(get_tv_mode_css(), unsafe_allow_html=True)
    # Enable auto-refresh on TV mode
    st_autorefresh(interval=1000 * refresh_interval, key="tv_refresh_timer")
    render_tv_mode(trades_df, bulk_threshold, refresh_interval, enable_sound)
else:
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    if page == "📊 Dashboard":
        # Enable auto-refresh
        st_autorefresh(interval=1000 * refresh_interval, key="dashboard_refresh_timer")
        
        # Top Header layout
        col_title, col_clock = st.columns([7, 3])
        with col_title:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="font-size: 36px; color: #8b5cf6; filter: drop-shadow(0 0 10px #8b5cf6); margin-bottom: 5px;">📈</div>
                <div>
                    <h1 style="margin: 0; padding: 0; font-size: 32px; font-weight: 900; font-family: 'Outfit'; color: white; background: none; -webkit-text-fill-color: initial;">TradeNepse</h1>
                    <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 14px; font-family: 'Inter'; font-weight: 500;">
                        Smart Market Intelligence for NEPSE Investors
                    </p>
                </div>
                <div style="margin-left: 15px; margin-top: 5px; background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 20px; padding: 4px 12px; display: inline-flex; align-items: center; gap: 6px;">
                    <span style="color: #10b981; font-size: 8px; animation: blinker 1.5s linear infinite;">●</span>
                    <span style="color: #10b981; font-weight: 700; font-size: 11px; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">Live Feed Active</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_clock:
            now_str = datetime.now().strftime("%I:%M:%S %p")
            date_str = datetime.now().strftime("%a, %b %d, %Y")
            st.markdown(f"""
            <div style="background-color: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 10px 18px; display: flex; align-items: center; gap: 12px; justify-content: flex-end; height: 100%; max-width: 320px; margin-left: auto;">
                <span style="font-size: 18px; color: #8B5CF6;">🕒</span>
                <div style="text-align: right;">
                    <div style="font-family: 'Roboto Mono', monospace; font-size: 15px; font-weight: 700; color: white; line-height: 1.2;">{now_str}</div>
                    <div style="font-size: 11px; color: #94A3B8; line-height: 1.2; font-family: 'Inter'; font-weight: 500;">{date_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
                
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
        
        # Render the full dashboard layout (filters, cards, panels, table, side activity panel)
        render_live_dashboard(trades_df, bulk_threshold, enable_sound)
        
    elif page == "🔥 Hot Stocks":
        st_autorefresh(interval=1000 * refresh_interval, key="hot_stocks_refresh_timer")
        render_hot_bulk_stocks_page(trades_df, bulk_threshold)
        
    elif page == "💰 Largest Trades":
        st_autorefresh(interval=1000 * refresh_interval, key="largest_trades_refresh_timer")
        render_largest_trades_page(trades_df, bulk_threshold)
        
    elif page == "📈 Symbol Analytics":
        render_symbol_analytics_page(trades_df, bulk_threshold)
        
    elif page == "🚨 Live Alerts":
        st_autorefresh(interval=1000 * refresh_interval, key="live_alerts_refresh_timer")
        render_live_alerts_page(trades_df, bulk_threshold)
        
    elif page == "🎯 Trade Planner (Coming Soon)":
        render_coming_soon_page("Trade Planner", "🎯")
        
    elif page == "🤖 Market Scanner (Coming Soon)":
        render_coming_soon_page("Market Scanner", "🤖")
