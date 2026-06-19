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
from analytics.schedule import market_is_open, get_market_status

# Check and initialize TV/Admin Mode session state
query_params = st.query_params
if "page" in query_params and query_params["page"] == "tv":
    st.session_state.tv_mode = True

is_tv_mode = st.session_state.get("tv_mode", False)
is_admin_route = query_params.get("page") == "adminloot" or "adminloot" in query_params
sidebar_state = "collapsed" if (is_tv_mode or is_admin_route) else "expanded"

# 1. Page Config
st.set_page_config(
    page_title="TradeNepse",
    layout="wide",
    initial_sidebar_state=sidebar_state
)

# Load current settings
settings = load_settings()
import pytz
tz_name = settings.get("timezone", "Asia/Kathmandu")
try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("Asia/Kathmandu")

data_folder = settings.get("data_folder", "data")

# Read refresh interval from settings.json (supporting both legacy refresh_interval and refresh_interval_seconds)
refresh_interval = st.session_state.get(
    "refresh_interval", 
    settings.get("refresh_interval_seconds", settings.get("refresh_interval", 15))
)
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
        active_business_date = datetime.now(tz).strftime("%Y-%m-%d")

csv_path = get_csv_path(active_business_date, data_folder)
trades_df = read_today_trades(csv_path)

# -------------------------------------------------------------
# Secure Admin Access Routing
# -------------------------------------------------------------
if is_admin_route:
    # 1. Render password lock screen if not authenticated
    if not st.session_state.get("admin_authenticated", False):
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)
        col_space, col_card, col_space_r = st.columns([3.5, 3.0, 3.5])
        with col_card:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 56px; filter: drop-shadow(0 0 10px #7C3AED);">⚙️</div>
                <h2 style="font-family: 'Outfit'; font-weight: 800; color: white; margin-top: 10px; margin-bottom: 5px;">TradeNepse Admin Access</h2>
                <p style="color: #64748B; font-size: 13px; font-family: 'Inter'; font-weight: 500;">Secure Portal Control</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("secure_admin_login_form"):
                input_pass = st.text_input("Admin Password", type="password", key="admin_route_pass_field")
                submit_login = st.form_submit_button("Authenticate Access", use_container_width=True)
                
                if submit_login:
                    configured_pass = settings.get("admin_password", "nepse_admin123")
                    if input_pass == configured_pass:
                        st.session_state.admin_authenticated = True
                        st.rerun()
                    else:
                        st.error("Access Denied")
                        st.stop()
            st.stop()
            
    # 2. Render authenticated Admin Control Workspace
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    col_title, col_logout = st.columns([8.2, 1.8])
    with col_title:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="font-size: 32px; color: #8b5cf6; filter: drop-shadow(0 0 10px #8b5cf6);">⚙️</div>
            <div>
                <h1 style="margin: 0; padding: 0; font-size: 28px; font-weight: 900; font-family: 'Outfit'; color: white;">TradeNepse Admin Control Workspace</h1>
                <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 13px; font-family: 'Inter';">
                    Secure System Architecture & Schedule Overrides Control Center
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("Log Out Admin", type="primary", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.query_params.clear()
            st.rerun()
            
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    from dashboard.views import render_admin_loot_workspace
    render_admin_loot_workspace(settings)
    st.stop()

# 4. Standard Navigation & Sidebar Layout (Public Area)
page = "📊 Dashboard"

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
        
        # Option Menu sidebar list (Public Options Only)
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
    # Enable auto-refresh on TV mode only during market hours and if enabled
    if settings.get("enable_auto_refresh", True) and market_is_open():
        st_autorefresh(interval=1000 * refresh_interval, key="tv_refresh_timer")
    render_tv_mode(trades_df, bulk_threshold, refresh_interval, enable_sound)
else:
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    if page == "📊 Dashboard":
        # Enable auto-refresh only during market hours and if enabled
        if settings.get("enable_auto_refresh", True) and market_is_open():
            st_autorefresh(interval=1000 * refresh_interval, key="dashboard_refresh_timer")
        
        # Top Header layout
        col_title, col_clock = st.columns([7, 3])
        
        # Compile dynamic market status layout
        market_status_text = get_market_status()
        
        if "Open" in market_status_text:
            badge_bg = "rgba(16, 185, 129, 0.1)"
            badge_border = "#10b981"
            badge_color = "#10b981"
            dot_animation = "animation: blinker 1.5s linear infinite;"
        elif "Holiday" in market_status_text:
            badge_bg = "rgba(239, 68, 68, 0.1)"
            badge_border = "#ef4444"
            badge_color = "#ef4444"
            dot_animation = ""
        else:
            badge_bg = "rgba(245, 158, 11, 0.1)"
            badge_border = "#f59e0b"
            badge_color = "#f59e0b"
            dot_animation = ""
            
        with col_title:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="font-size: 36px; color: #8b5cf6; filter: drop-shadow(0 0 10px #8b5cf6); margin-bottom: 5px;">📈</div>
                <div>
                    <h1 style="margin: 0; padding: 0; font-size: 32px; font-weight: 900; font-family: 'Outfit'; color: white; background: none; -webkit-text-fill-color: initial;">TradeNepse</h1>
                    <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 14px; font-family: 'Inter'; font-weight: 500;">
                        Smart Market Intelligence for NEPSE Investors
                    </p>
                </div>
                <div style="margin-left: 15px; margin-top: 5px; background-color: {badge_bg}; border: 1px solid {badge_border}; border-radius: 20px; padding: 4px 12px; display: inline-flex; align-items: center; gap: 6px;">
                    <span style="color: {badge_color}; font-size: 8px; {dot_animation}">●</span>
                    <span style="color: {badge_color}; font-weight: 700; font-size: 11px; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">{market_status_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_clock:
            now_str = datetime.now(tz).strftime("%I:%M:%S %p")
            date_str = datetime.now(tz).strftime("%a, %b %d, %Y")
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
        if settings.get("enable_auto_refresh", True) and market_is_open():
            st_autorefresh(interval=1000 * refresh_interval, key="hot_stocks_refresh_timer")
        render_hot_bulk_stocks_page(trades_df, bulk_threshold)
        
    elif page == "💰 Largest Trades":
        if settings.get("enable_auto_refresh", True) and market_is_open():
            st_autorefresh(interval=1000 * refresh_interval, key="largest_trades_refresh_timer")
        render_largest_trades_page(trades_df, bulk_threshold)
        
    elif page == "📈 Symbol Analytics":
        render_symbol_analytics_page(trades_df, bulk_threshold)
        
    elif page == "🚨 Live Alerts":
        if settings.get("enable_auto_refresh", True) and market_is_open():
            st_autorefresh(interval=1000 * refresh_interval, key="live_alerts_refresh_timer")
        render_live_alerts_page(trades_df, bulk_threshold)
        
    elif page == "🎯 Trade Planner (Coming Soon)":
        render_coming_soon_page("Trade Planner", "🎯")
        
    elif page == "🤖 Market Scanner (Coming Soon)":
        render_coming_soon_page("Market Scanner", "🤖")
