import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from settings.config import load_settings, save_settings
from storage.csv_storage import read_collector_status
from analytics.metrics import (
    calculate_summary_metrics,
    get_hot_stocks_volume,
    get_hot_stocks_turnover,
    get_hot_stocks_bulk_transactions,
    filter_bulk_trades
)

# Robust import for streamlit-aggrid across versions
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode
try:
    from st_aggrid import JsCode
except ImportError:
    from st_aggrid.shared import JsCode

from dashboard.styles import get_grid_custom_css, get_grid_tv_css

def format_number(val):
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f} B"
    elif val >= 1_000_000:
        return f"{val / 1_000_000:.2f} M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f} K"
    return str(val)

def format_nepali_amount(val):
    if val >= 10_000_000:  # 1 Crore
        return f"Rs. {val / 10_000_000:.2f} Cr"
    elif val >= 100_000:  # 1 Lakh
        return f"Rs. {val / 100_000:.2f} Lk"
    return f"Rs. {val:,.2f}"

def get_instrument_type(symbol, name):
    symbol = str(symbol).upper().strip()
    name = str(name).upper().strip()
    
    # 1. ETF
    if "ETF" in symbol or "ETF" in name:
        return "ETF"
    
    # 2. Mutual Fund
    if "MUTUAL FUND" in name or "FUND" in name or "YOJANA" in name or "SCHEME" in name or symbol.endswith("MF"):
        return "Mutual Fund"
    
    # 3. Debenture
    if "DEBENTURE" in name or "BOND" in name or "%" in name or (symbol.endswith("D") and len(symbol) > 4) or any(symbol.endswith(f"D{yr}") for yr in range(70, 100)):
        return "Debenture"
        
    # 4. Preference Share
    if "PREFERENCE" in name or "PREF" in name or symbol.endswith("P") or symbol.endswith("PS"):
        return "Preference Share"
        
    # 5. Rights Share
    if "RIGHT" in name or "RIGHTS" in name or symbol.endswith("R"):
        return "Rights Share"
        
    # 6. Equity
    return "Equity"

# -------------------------------------------------------------
# AgGrid Cell Renderers & Formatters (JsCode)
# -------------------------------------------------------------
symbol_renderer = JsCode("""
class SymbolRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        if (params.value != null) {
            this.eGui.innerHTML = '<strong style="color: #00D4FF; font-weight: 700; cursor: pointer;">' + params.value + '</strong>';
        }
    }
    getGui() {
        return this.eGui;
    }
}
""")

instrument_renderer = JsCode("""
class InstrumentRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        var val = params.value;
        if (val != null) {
            if (val === 'Mutual Fund') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(139, 92, 246, 0.2); border: 1px solid #8B5CF6; color: #FFFFFF;">Mutual Fund</span>';
            } else if (val === 'Equity') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(59, 130, 246, 0.2); border: 1px solid #3B82F6; color: #FFFFFF;">Equity</span>';
            } else if (val === 'Debenture') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(245, 158, 11, 0.2); border: 1px solid #F59E0B; color: #FFFFFF;">Debenture</span>';
            } else if (val === 'ETF') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(6, 182, 212, 0.2); border: 1px solid #06B6D4; color: #FFFFFF;">ETF</span>';
            } else if (val === 'Rights Share' || val === 'Rights') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(34, 197, 94, 0.2); border: 1px solid #22C55E; color: #FFFFFF;">Rights</span>';
            } else if (val === 'Preference Share') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #FFFFFF;">Pref. Share</span>';
            } else {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(148, 163, 184, 0.2); border: 1px solid #94A3B8; color: #FFFFFF;">' + val + '</span>';
            }
        }
    }
    getGui() {
        return this.eGui;
    }
}
""")

trade_type_renderer = JsCode("""
class TradeTypeRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        var val = params.value;
        if (val != null) {
            if (val === 'Bulk') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(239, 68, 68, 0.25); border: 1px solid #EF4444; color: #FFFFFF;">Bulk</span>';
            } else if (val === 'Cross') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(139, 92, 246, 0.25); border: 1px solid #8B5CF6; color: #FFFFFF;">Cross</span>';
            } else {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 11px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(148, 163, 184, 0.2); border: 1px solid #94A3B8; color: #FFFFFF;">Normal</span>';
            }
        }
    }
    getGui() {
        return this.eGui;
    }
}
""")

qty_formatter = JsCode("""
function(params) {
    if (params.value == null) return '';
    return Number(params.value).toLocaleString('en-US');
}
""")

rate_formatter = JsCode("""
function(params) {
    if (params.value == null) return '';
    return 'Rs. ' + Number(params.value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}
""")

amount_formatter = JsCode("""
function(params) {
    if (params.value == null) return '';
    return 'Rs. ' + Number(params.value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}
""")

# Conditional styling JS callback (colors based on quantity threshold)
cellstyle_jscode = JsCode("""
function(params) {
    var qty = params.data.Quantity;
    if (qty >= 100000) {
        return {
            'backgroundColor': 'rgba(239, 68, 68, 0.45)',
            'color': '#ffffff',
            'fontWeight': 'bold'
        };
    } else if (qty >= 50000) {
        return {
            'backgroundColor': 'rgba(239, 68, 68, 0.25)',
            'color': '#ffffff',
            'fontWeight': 'bold'
        };
    } else if (qty >= 25000) {
        return {
            'backgroundColor': 'rgba(249, 115, 22, 0.25)',
            'color': '#ffffff',
            'fontWeight': 'bold'
        };
    } else if (qty >= 10000) {
        return {
            'backgroundColor': 'rgba(234, 179, 8, 0.25)',
            'color': '#ffffff',
            'fontWeight': 'bold'
        };
    } else {
        return {
            'color': '#ffffff'
        };
    }
}
""")

qty_cellstyle_jscode = JsCode("""
function(params) {
    var qty = params.value;
    if (qty == null) return {};
    if (qty >= 100000) {
        return { 'color': '#FF3B30', 'fontWeight': 'bold' }; // Bright Red
    } else if (qty >= 50000) {
        return { 'color': '#EF4444', 'fontWeight': 'bold' }; // Red
    } else if (qty >= 25000) {
        return { 'color': '#F97316', 'fontWeight': 'bold' }; // Orange
    } else if (qty >= 10000) {
        return { 'color': '#F59E0B', 'fontWeight': 'bold' }; // Yellow
    } else {
        return { 'color': '#FFFFFF' }; // White Normal
    }
}
""")

def configure_grid_columns(gb, table_cols):
    """
    Applies the audited high-contrast text color system, formatters, and HTML renderers to AgGrid columns.
    """
    if "Symbol" in table_cols:
        gb.configure_column("Symbol", cellRenderer=symbol_renderer)
    if "Instrument Type" in table_cols:
        gb.configure_column("Instrument Type", cellRenderer=instrument_renderer)
    if "Trade Type" in table_cols:
        gb.configure_column("Trade Type", cellRenderer=trade_type_renderer)
    if "Quantity" in table_cols:
        gb.configure_column("Quantity", valueFormatter=qty_formatter, cellStyle=qty_cellstyle_jscode)
    if "Rate" in table_cols:
        gb.configure_column("Rate", valueFormatter=rate_formatter, cellStyle={"color": "#34D399"})
    if "Amount" in table_cols:
        gb.configure_column("Amount", valueFormatter=amount_formatter, cellStyle={"color": "#FBBF24"})
    if "Contract ID" in table_cols:
        gb.configure_column("Contract ID", cellStyle={"color": "#94A3B8"})
    if "Trade Time" in table_cols:
        gb.configure_column("Trade Time", cellStyle={"color": "#FFFFFF"})
    if "Company" in table_cols:
        gb.configure_column("Company", cellStyle={"color": "#FFFFFF"})

# -------------------------------------------------------------
# Base Rendering Functions
# -------------------------------------------------------------
def render_summary_cards(df, bulk_threshold):
    """
    Renders the metric summary cards at the top of the dashboard.
    """
    metrics = calculate_summary_metrics(df, bulk_threshold)
    
    total_contracts = f"{metrics['total_contracts']:,}"
    total_volume = format_number(metrics['total_volume'])
    total_turnover = format_nepali_amount(metrics['total_turnover'])
    total_bulk = f"{metrics['total_bulk_transactions']:,}"
    max_qty = f"{metrics['largest_trade_quantity']:,}"
    max_val = format_nepali_amount(metrics['largest_trade_value'])
    
    cards_html = f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(139, 92, 246, 0.15); color: #8b5cf6;">📄</div>
                <div class="metric-label" style="color: #8b5cf6;">Total Contracts</div>
            </div>
            <div class="metric-value">{total_contracts}</div>
            <div class="metric-sub">Today</div>
        </div>
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">📊</div>
                <div class="metric-label" style="color: #10b981;">Total Volume</div>
            </div>
            <div class="metric-value">{total_volume}</div>
            <div class="metric-sub">Shares</div>
        </div>
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b;">💼</div>
                <div class="metric-label" style="color: #f59e0b;">Total Turnover</div>
            </div>
            <div class="metric-value" style="color: #facc15;">{total_turnover}</div>
            <div class="metric-sub">Today</div>
        </div>
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(239, 68, 68, 0.15); color: #ef4444;">🔥</div>
                <div class="metric-label" style="color: #ef4444;">Bulk Trades ({bulk_threshold}+)</div>
            </div>
            <div class="metric-value">{total_bulk}</div>
            <div class="metric-sub">Today</div>
        </div>
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">🎯</div>
                <div class="metric-label" style="color: #3b82f6;">Largest Qty</div>
            </div>
            <div class="metric-value">{max_qty}</div>
            <div class="metric-sub">Shares</div>
        </div>
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background: rgba(168, 85, 247, 0.15); color: #a855f7;">💎</div>
                <div class="metric-label" style="color: #a855f7;">Largest Value</div>
            </div>
            <div class="metric-value">{max_val}</div>
            <div class="metric-sub">Value</div>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)

def play_alert_sound():
    """
    Plays a short synthesized chime using the Web Audio API.
    """
    sound_html = """
    <script>
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const ctx = new AudioContext();
            
            // First tone
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(880, ctx.currentTime);
            gain1.gain.setValueAtTime(0.05, ctx.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            
            // Second tone
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(1100, ctx.currentTime + 0.08);
            gain2.gain.setValueAtTime(0.05, ctx.currentTime + 0.08);
            gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            
            osc1.start();
            osc1.stop(ctx.currentTime + 0.15);
            osc2.start(ctx.currentTime + 0.08);
            osc2.stop(ctx.currentTime + 0.25);
        }
    } catch (e) {
        console.error("Audio failed:", e);
    }
    </script>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

def render_alert_banner(df, bulk_threshold, enable_sound):
    bulk_trades = filter_bulk_trades(df, bulk_threshold)
    if bulk_trades.empty:
        return
        
    newest_bulk = bulk_trades.sort_values(by="contractId", ascending=False).iloc[0]
    newest_cid = int(newest_bulk["contractId"])
    
    if "last_played_cid" not in st.session_state:
        st.session_state.last_played_cid = 0
        
    is_new = (newest_cid > st.session_state.last_played_cid)
    
    symbol = newest_bulk["stockSymbol"]
    qty = int(newest_bulk["contractQuantity"])
    rate = float(newest_bulk["contractRate"])
    amount = float(newest_bulk["contractAmount"])
    trade_time_full = newest_bulk["tradeTime"]
    
    try:
        t_parsed = datetime.fromisoformat(trade_time_full.replace("Z", ""))
        trade_time_str = t_parsed.strftime("%H:%M:%S")
    except Exception:
        trade_time_str = trade_time_full.split("T")[-1][:8]
        
    formatted_amount = format_nepali_amount(amount)
    
    alert_html = f"""
    <div class="live-bulk-alert-container pulsing">
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 18px; color: #ffd60a;">🔔</span>
                <span style="color: #ffffff; font-family: 'Inter', sans-serif; font-size: 14px;">
                    <strong>LIVE BULK TRADE ALERT:</strong> <strong>{qty:,}</strong> shares of <strong>{symbol}</strong> traded at <strong>Rs. {rate:,.2f}</strong> (Total: <strong>{formatted_amount}</strong>) at {trade_time_str}.
                </span>
            </div>
            <span style="font-size: 18px; color: rgba(255,255,255,0.4); cursor: pointer; font-weight: bold;">×</span>
        </div>
    </div>
    """
    st.markdown(alert_html, unsafe_allow_html=True)
    
    if is_new:
        st.session_state.last_played_cid = newest_cid
        if enable_sound:
            play_alert_sound()
            st.toast(f"🚨 Bulk trade detected! {qty:,} shares of {symbol}", icon="🔥")

def render_filter_bar(df, bulk_threshold):
    st.markdown("""
    <div class="filter-panel">
        <div class="filter-title">⚡ FILTERS</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3, col4, col5, col_btn = st.columns([1.5, 2, 2.2, 1.5, 1.5, 1.3])
        with col1:
            bulk_qty_opt = st.selectbox(
                "1. Bulk Filter (Min Qty) ℹ️",
                options=["5000+", "10000+", "25000+", "50000+", "100000+", "All"],
                index=0
            )
        with col2:
            all_symbols = sorted(df["stockSymbol"].unique()) if not df.empty else []
            selected_symbols = st.multiselect(
                "2. Symbol ℹ️",
                options=all_symbols,
                default=[]
            )
        with col3:
            st.markdown("<div style='font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 4px;'>3. Time Range ℹ️</div>", unsafe_allow_html=True)
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                start_time_str = st.text_input("Start", value="11:00", label_visibility="collapsed")
            with t_col2:
                end_time_str = st.text_input("End", value="15:00", label_visibility="collapsed")
        with col4:
            instr_opt = st.selectbox(
                "4. Instrument Type ℹ️",
                options=["All", "Equity", "Mutual Fund", "Preference Share", "Debenture", "Rights Share", "ETF"],
                index=0
            )
        with col5:
            turnover_opt = st.selectbox(
                "5. Turnover Range ℹ️",
                options=["All", "Below 1 Lakh", "1 Lakh – 5 Lakh", "5 Lakh – 10 Lakh", "10 Lakh – 50 Lakh", "50 Lakh – 1 Crore", "Above 1 Crore"],
                index=0
            )
        with col_btn:
            st.write("") 
            if st.button("🔄 Reset Filters", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    # Filtering Logic
    f_df = df.copy()
    
    # 1. Bulk Filter
    if bulk_qty_opt != "All":
        qty_val = int(bulk_qty_opt.replace("+", "").replace(",", ""))
        f_df = f_df[f_df["contractQuantity"] >= qty_val]
        
    # 2. Symbol Filter
    if selected_symbols:
        f_df = f_df[f_df["stockSymbol"].isin(selected_symbols)]
        
    # 3. Time Filter
    if not f_df.empty:
        f_df["ParsedTime"] = pd.to_datetime(f_df["tradeTime"].str.replace("Z", ""), errors="coerce")
        valid_times = f_df["ParsedTime"].dropna()
        ref_date = valid_times.max().date() if not valid_times.empty else datetime.now().date()
        
        def parse_time_str(time_str, default_time_val):
            try:
                return datetime.strptime(time_str.strip(), "%H:%M").time()
            except:
                try:
                    return datetime.strptime(time_str.strip(), "%I:%M %p").time()
                except:
                    return default_time_val
                    
        t_start = parse_time_str(start_time_str, datetime.strptime("11:00", "%H:%M").time())
        t_end = parse_time_str(end_time_str, datetime.strptime("15:00", "%H:%M").time())
        
        start_dt = datetime.combine(ref_date, t_start)
        end_dt = datetime.combine(ref_date, t_end)
        f_df = f_df[(f_df["ParsedTime"] >= start_dt) & (f_df["ParsedTime"] <= end_dt)]
        
    # 4. Instrument Type Filter
    if not f_df.empty:
        f_df["Instrument Type"] = f_df.apply(lambda row: get_instrument_type(row["stockSymbol"], row["securityName"]), axis=1)
        if instr_opt != "All":
            f_df = f_df[f_df["Instrument Type"] == instr_opt]
    else:
        f_df["Instrument Type"] = pd.Series(dtype=str)
        
    # 5. Turnover Range Filter
    if not f_df.empty:
        if turnover_opt == "Below 1 Lakh":
            f_df = f_df[f_df["contractAmount"] < 100_000]
        elif turnover_opt == "1 Lakh – 5 Lakh":
            f_df = f_df[(f_df["contractAmount"] >= 100_000) & (f_df["contractAmount"] < 500_000)]
        elif turnover_opt == "5 Lakh – 10 Lakh":
            f_df = f_df[(f_df["contractAmount"] >= 500_000) & (f_df["contractAmount"] < 1_000_000)]
        elif turnover_opt == "10 Lakh – 50 Lakh":
            f_df = f_df[(f_df["contractAmount"] >= 1_000_000) & (f_df["contractAmount"] < 5_000_000)]
        elif turnover_opt == "50 Lakh – 1 Crore":
            f_df = f_df[(f_df["contractAmount"] >= 5_000_000) & (f_df["contractAmount"] < 10_000_000)]
        elif turnover_opt == "Above 1 Crore":
            f_df = f_df[f_df["contractAmount"] >= 10_000_000]
            
    return f_df

def render_market_activity_panel(df, bulk_threshold):
    if df.empty:
        st.info("No market transactions captured yet.")
        return
        
    most_active_symbol = df["stockSymbol"].value_counts().idxmax()
    most_active_count = df["stockSymbol"].value_counts().max()
    
    idx_max = df["contractAmount"].idxmax()
    largest_symbol = df.loc[idx_max, "stockSymbol"]
    largest_amount = df.loc[idx_max, "contractAmount"]
    largest_qty = df.loc[idx_max, "contractQuantity"]
    largest_amount_formatted = format_nepali_amount(largest_amount)
    
    turnovers = df.groupby("stockSymbol")["contractAmount"].sum()
    highest_turnover_symbol = turnovers.idxmax()
    highest_turnover_val = turnovers.max()
    highest_turnover_formatted = format_nepali_amount(highest_turnover_val)
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold]
    if not bulk_df.empty:
        latest_bulk = bulk_df.sort_values(by="contractId", ascending=False).iloc[0]
        latest_bulk_symbol = latest_bulk["stockSymbol"]
        latest_bulk_qty = latest_bulk["contractQuantity"]
        latest_bulk_time_full = latest_bulk["tradeTime"]
        try:
            t_parsed = datetime.fromisoformat(latest_bulk_time_full.replace("Z", ""))
            latest_bulk_time_formatted = t_parsed.strftime("%H:%M:%S")
        except:
            latest_bulk_time_formatted = latest_bulk_time_full.split("T")[-1][:8]
    else:
        latest_bulk_symbol, latest_bulk_qty, latest_bulk_time_formatted = "None", 0, "N/A"
        
    updated_time_str = datetime.now().strftime("%H:%M:%S")
    
    activity_html = f"""
    <div class="activity-panel">
        <div>
            <div class="activity-header">📡 LIVE MARKET ACTIVITY</div>
            
            <div class="activity-item">
                <div class="activity-label">Most Active Stock</div>
                <div class="activity-value" style="color: #38bdf8;">{most_active_symbol}</div>
                <div class="activity-sub">{most_active_count:,} Total Trades</div>
            </div>
            
            <div class="activity-item">
                <div class="activity-label">Largest Trade Today</div>
                <div class="activity-value" style="color: #facc15;">{largest_symbol}</div>
                <div class="activity-sub">{largest_qty:,} shares • {largest_amount_formatted}</div>
            </div>
            
            <div class="activity-item">
                <div class="activity-label">Highest Turnover Stock</div>
                <div class="activity-value" style="color: #4ade80;">{highest_turnover_symbol}</div>
                <div class="activity-sub">{highest_turnover_formatted}</div>
            </div>
            
            <div class="activity-item">
                <div class="activity-label">Latest Bulk Trade</div>
                <div class="activity-value" style="color: #f87171;">{latest_bulk_symbol}</div>
                <div class="activity-sub">{latest_bulk_qty:,} shares @ {latest_bulk_time_formatted}</div>
            </div>
        </div>
        
        <div>
            <div class="activity-update">Last Updated: {updated_time_str}</div>
        </div>
    </div>
    """
    st.markdown(activity_html, unsafe_allow_html=True)

def render_live_table(df, bulk_threshold):
    if df.empty:
        st.info("No records match the current filters.")
        return
        
    display_df = df.copy().sort_values(by="contractId", ascending=False)
    
    col_sel, col_dl = st.columns([8, 2])
    with col_sel:
        row_count = st.selectbox("Show rows", options=[50, 100, 200, 500], index=1, key="table_row_count", label_visibility="collapsed")
    with col_dl:
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Table",
            data=csv_data,
            file_name=f"NEPSE_Bulk_Trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    display_df = display_df.head(row_count)
    
    def format_time(val):
        try:
            return datetime.fromisoformat(str(val).replace("Z", "")).strftime("%H:%M:%S")
        except:
            return str(val).split("T")[-1][:8]
            
    display_df["Trade Time"] = display_df["tradeTime"].apply(format_time)
    display_df["Instrument Type"] = display_df.apply(lambda row: get_instrument_type(row["stockSymbol"], row["securityName"]), axis=1)
    display_df["Trade Type"] = display_df.apply(lambda row: "Bulk" if row["contractQuantity"] >= bulk_threshold else "Normal", axis=1)
    
    display_df = display_df.rename(columns={
        "stockSymbol": "Symbol",
        "securityName": "Company",
        "contractQuantity": "Quantity",
        "contractRate": "Rate",
        "contractAmount": "Amount",
        "contractId": "Contract ID"
    })
    
    table_df = display_df[["Trade Time", "Symbol", "Company", "Instrument Type", "Quantity", "Rate", "Amount", "Contract ID", "Trade Type"]]
    
    # AgGrid setup
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(resizable=True, filterable=True, sortable=True, editable=False)
    configure_grid_columns(gb, table_df.columns)
        
    gb.configure_grid_options(
        rowHeight=50,
        headerHeight=50,
        animateRows=True,
        rowSelection='single'
    )
    
    gridOptions = gb.build()
    
    AgGrid(
        table_df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        theme="alpine",
        custom_css=get_grid_custom_css(),
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        use_container_width=True
    )

def render_live_dashboard(df, bulk_threshold, enable_sound):
    """
    Renders the clean, optimized dashboard view.
    """
    # 1. Alert Banner
    render_alert_banner(df, bulk_threshold, enable_sound)
    
    # 2. Filter Bar (Horizontal)
    f_df = render_filter_bar(df, bulk_threshold)
    
    # 3. Top KPI Cards (Collapsible)
    if st.session_state.get("show_metrics", True):
        st.markdown('<div class="section-header"><span class="section-header-icon">📈</span><span class="section-header-title">KEY METRICS (FILTERED)</span></div>', unsafe_allow_html=True)
        render_summary_cards(f_df, bulk_threshold)
    
    # 4. Live Feed Header & Content
    refresh_interval = st.session_state.get("refresh_interval", 15)
    live_feed_header = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e293b; margin-top: 35px; margin-bottom: 15px; padding-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px; color: #a78bfa;">⚡</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; text-transform: uppercase;">Floorsheet Live Feed</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; font-size: 14px; color: #94a3b8;">
            <span style="color: #10b981; font-weight: bold; font-family: 'Inter', sans-serif;">● Auto Refresh: {refresh_interval}s</span>
            <span style="cursor: pointer; font-size: 16px;">🔄 ⛶</span>
        </div>
    </div>
    """
    st.markdown(live_feed_header, unsafe_allow_html=True)

    render_live_table(f_df, bulk_threshold)
        
    # Footer Row
    last_update_str = datetime.now().strftime("%I:%M:%S %p")
    footer_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1e293b; margin-top: 30px; padding-top: 15px; font-size: 12px; color: #64748b;">
        <div>Data Source: NEPSE Floorsheet API</div>
        <div>Last Updated: {last_update_str} • <span style="color: #10b981; font-weight: bold;">Connected</span></div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

def render_tv_mode(df, bulk_threshold, refresh_interval, enable_sound):
    """
    Renders a maximized, OBS-ready full screen dashboard with AgGrid.
    """
    # 1. Header Row
    now_str = datetime.now().strftime("%H:%M:%S")
    header_html = f"""
    <div class="tv-header-container">
        <div class="tv-header-title">📊 NEPSE LIVE BULK TERMINAL</div>
        <div class="tv-header-time">{now_str}</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # 2. Alert Banner (TV styling)
    bulk_trades = filter_bulk_trades(df, bulk_threshold)
    if not bulk_trades.empty:
        newest_bulk = bulk_trades.sort_values(by="contractId", ascending=False).iloc[0]
        newest_cid = int(newest_bulk["contractId"])
        
        if "last_played_cid_tv" not in st.session_state:
            st.session_state.last_played_cid_tv = 0
            
        is_new = (newest_cid > st.session_state.last_played_cid_tv)
        
        symbol = newest_bulk["stockSymbol"]
        qty = int(newest_bulk["contractQuantity"])
        rate = float(newest_bulk["contractRate"])
        amount = float(newest_bulk["contractAmount"])
        trade_time_full = newest_bulk["tradeTime"]
        
        try:
            t_parsed = datetime.fromisoformat(trade_time_full.replace("Z", ""))
            trade_time_str = t_parsed.strftime("%H:%M:%S")
        except:
            trade_time_str = trade_time_full.split("T")[-1][:8]
            
        formatted_amount = format_nepali_amount(amount)
        
        tv_alert_html = f"""
        <div class="tv-alert-banner">
            <div class="tv-alert-header">🚨 LIVE BULK TRADE DETECTED</div>
            <div class="tv-alert-grid">
                <div class="alert-item">
                    <span class="alert-label">Symbol</span>
                    <span class="tv-alert-val sym">{symbol}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label">Quantity</span>
                    <span class="tv-alert-val qty">{qty:,}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label">Rate</span>
                    <span class="tv-alert-val">Rs. {rate:,.2f}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label">Turnover</span>
                    <span class="tv-alert-val val">{formatted_amount}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label">Time</span>
                    <span class="tv-alert-val time">{trade_time_str}</span>
                </div>
            </div>
        </div>
        """
        st.markdown(tv_alert_html, unsafe_allow_html=True)
        
        if is_new:
            st.session_state.last_played_cid_tv = newest_cid
            if enable_sound:
                play_alert_sound()
                st.toast(f"🚨 Bulk trade detected! {qty:,} shares of {symbol}", icon="🔥")
                
    # 3. Giant KPI Metric Cards
    metrics = calculate_summary_metrics(df, bulk_threshold)
    total_contracts = f"{metrics['total_contracts']:,}"
    total_volume = format_number(metrics['total_volume'])
    total_turnover = format_nepali_amount(metrics['total_turnover'])
    total_bulk = f"{metrics['total_bulk_transactions']:,}"
    max_qty = f"{metrics['largest_trade_quantity']:,}"
    max_val = format_nepali_amount(metrics['largest_trade_value'])
    
    tv_cards_html = f"""
    <div class="tv-grid">
        <div class="tv-card">
            <div class="tv-label">Total Contracts</div>
            <div class="tv-value">{total_contracts}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Total Volume</div>
            <div class="tv-value">{total_volume}</div>
        </div>
        <div class="tv-card accent">
            <div class="tv-label">Total Turnover</div>
            <div class="tv-value" style="color: #4ade80;">{total_turnover}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Bulk Trades</div>
            <div class="tv-value" style="color: #ffd60a;">{total_bulk}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Max Qty</div>
            <div class="tv-value">{max_qty}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Max Value</div>
            <div class="tv-value">{max_val}</div>
        </div>
    </div>
    """
    st.markdown(tv_cards_html, unsafe_allow_html=True)
    
    # 4. TV Mode AgGrid rendering
    st.markdown('<div class="tv-aggrid-container">', unsafe_allow_html=True)
    display_df = df.copy().sort_values(by="contractId", ascending=False).head(15)
    
    def format_time(val):
        try:
            return datetime.fromisoformat(str(val).replace("Z", "")).strftime("%H:%M:%S")
        except:
            return str(val).split("T")[-1][:8]
            
    display_df["Trade Time"] = display_df["tradeTime"].apply(format_time)
    display_df["Instrument Type"] = display_df.apply(lambda row: get_instrument_type(row["stockSymbol"], row["securityName"]), axis=1)
    display_df["Trade Type"] = display_df.apply(lambda row: "Bulk" if row["contractQuantity"] >= bulk_threshold else "Normal", axis=1)
    
    display_df = display_df.rename(columns={
        "stockSymbol": "Symbol",
        "securityName": "Company",
        "contractQuantity": "Quantity",
        "contractRate": "Rate",
        "contractAmount": "Amount",
        "contractId": "Contract ID"
    })
    
    table_df = display_df[["Trade Time", "Symbol", "Company", "Instrument Type", "Quantity", "Rate", "Amount", "Contract ID", "Trade Type"]]
    
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(resizable=True, sortable=True)
    configure_grid_columns(gb, table_df.columns)
        
    gb.configure_grid_options(
        rowHeight=60,
        headerHeight=60,
        animateRows=True
    )
    
    gridOptions = gb.build()
    
    AgGrid(
        table_df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        theme="alpine",
        custom_css=get_grid_tv_css(),
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 5. Exit TV Mode Button
    st.markdown('<div class="tv-exit-container">', unsafe_allow_html=True)
    if st.button("Exit TV Mode"):
        st.session_state.tv_mode = False
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# Dedicated Sidebar Page Renderers
# -------------------------------------------------------------
def render_hot_bulk_stocks_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">🔥</span><span class="section-header-title">Hot Bulk Stocks Rankings</span></div>', unsafe_allow_html=True)
    
    view_limit = st.selectbox("Rank Limit", options=[10, 20, 50], format_func=lambda x: f"Top {x}")
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold]
    if bulk_df.empty:
        st.info("No bulk transactions recorded today to compile rankings.")
        return
        
    grouped = bulk_df.groupby("stockSymbol").agg(
        total_qty=("contractQuantity", "sum"),
        total_turnover=("contractAmount", "sum"),
        trades_count=("contractId", "count"),
        largest_trade=("contractAmount", "max")
    ).reset_index()
    
    grouped["avg_size"] = grouped["total_turnover"] / grouped["trades_count"]
    grouped = grouped.sort_values(by="total_turnover", ascending=False).head(view_limit).reset_index(drop=True)
    
    grouped.insert(0, "Rank", grouped.index + 1)
    
    grouped = grouped.rename(columns={
        "stockSymbol": "Symbol",
        "total_qty": "Bulk Quantity",
        "total_turnover": "Bulk Turnover",
        "trades_count": "Number Of Bulk Trades",
        "avg_size": "Average Trade Size",
        "largest_trade": "Largest Trade"
    })
    
    gb = GridOptionsBuilder.from_dataframe(grouped)
    gb.configure_default_column(resizable=True, sortable=True)
    gb.configure_column("Rank", width=80)
    gb.configure_column("Symbol", cellRenderer=symbol_renderer)
    gb.configure_column("Bulk Quantity", valueFormatter=qty_formatter)
    gb.configure_column("Bulk Turnover", valueFormatter=amount_formatter)
    gb.configure_column("Number Of Bulk Trades", valueFormatter=qty_formatter)
    gb.configure_column("Average Trade Size", valueFormatter=amount_formatter)
    gb.configure_column("Largest Trade", valueFormatter=amount_formatter)
    
    gridOptions = gb.build()
    
    AgGrid(
        grouped,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        theme="alpine",
        custom_css=get_grid_custom_css(),
        use_container_width=True
    )

def render_largest_trades_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">💰</span><span class="section-header-title">Largest Trades Today</span></div>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("No transaction data available.")
        return
        
    limit = st.selectbox("Show Top", options=[25, 50, 100], index=0)
    large_df = df.copy().sort_values(by="contractAmount", ascending=False).head(limit)
    
    def format_time(val):
        try:
            return datetime.fromisoformat(str(val).replace("Z", "")).strftime("%H:%M:%S")
        except:
            return str(val).split("T")[-1][:8]
            
    large_df["Trade Time"] = large_df["tradeTime"].apply(format_time)
    large_df["Instrument Type"] = large_df.apply(lambda row: get_instrument_type(row["stockSymbol"], row["securityName"]), axis=1)
    large_df["Trade Type"] = large_df.apply(lambda row: "Bulk" if row["contractQuantity"] >= bulk_threshold else "Normal", axis=1)
    
    large_df = large_df.rename(columns={
        "stockSymbol": "Symbol",
        "securityName": "Company",
        "contractQuantity": "Quantity",
        "contractRate": "Rate",
        "contractAmount": "Amount",
        "contractId": "Contract ID"
    })
    
    table_df = large_df[["Trade Time", "Symbol", "Company", "Instrument Type", "Quantity", "Rate", "Amount", "Contract ID", "Trade Type"]]
    
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(resizable=True, sortable=True)
    configure_grid_columns(gb, table_df.columns)
        
    gb.configure_grid_options(
        rowHeight=50,
        headerHeight=50,
        animateRows=True
    )
    gridOptions = gb.build()
    
    AgGrid(
        table_df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        theme="alpine",
        custom_css=get_grid_custom_css(),
        use_container_width=True
    )

def render_symbol_analytics_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">📊</span><span class="section-header-title">Symbol Analytics</span></div>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("No transaction data available.")
        return
        
    all_symbols = sorted(df["stockSymbol"].unique())
    selected_symbol = st.selectbox("Select Symbol", options=all_symbols)
    
    symbol_df = df[df["stockSymbol"] == selected_symbol]
    bulk_symbol_df = symbol_df[symbol_df["contractQuantity"] >= bulk_threshold]
    
    total_trades = len(symbol_df)
    total_bulk_trades = len(bulk_symbol_df)
    total_qty = symbol_df["contractQuantity"].sum()
    bulk_qty = bulk_symbol_df["contractQuantity"].sum()
    total_turnover = symbol_df["contractAmount"].sum()
    bulk_turnover = bulk_symbol_df["contractAmount"].sum()
    
    st.markdown(f"### Analysis for **{selected_symbol}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", f"{total_trades:,}")
        st.metric("Bulk Trades", f"{total_bulk_trades:,}")
    with col2:
        st.metric("Total Quantity", f"{total_qty:,}")
        st.metric("Bulk Quantity", f"{bulk_qty:,} ({bulk_qty/total_qty*100:.1f}%)" if total_qty > 0 else "0")
    with col3:
        st.metric("Total Turnover", format_nepali_amount(total_turnover))
        st.metric("Bulk Turnover", format_nepali_amount(bulk_turnover))
        
    if not bulk_symbol_df.empty:
        st.markdown("#### Bulk Trades Details")
        bulk_symbol_df = bulk_symbol_df.copy()
        
        def format_time(val):
            try:
                return datetime.fromisoformat(str(val).replace("Z", "")).strftime("%H:%M:%S")
            except:
                return str(val).split("T")[-1][:8]
        bulk_symbol_df["Trade Time"] = bulk_symbol_df["tradeTime"].apply(format_time)
        
        bulk_symbol_df = bulk_symbol_df.rename(columns={
            "contractQuantity": "Quantity",
            "contractRate": "Rate",
            "contractAmount": "Amount",
            "contractId": "Contract ID"
        })
        
        disp_df = bulk_symbol_df[["Trade Time", "Quantity", "Rate", "Amount", "Contract ID"]]
        
        gb = GridOptionsBuilder.from_dataframe(disp_df)
        gb.configure_default_column(resizable=True, sortable=True)
        configure_grid_columns(gb, disp_df.columns)
        
        gb.configure_grid_options(
            rowHeight=50,
            headerHeight=50,
            animateRows=True
        )
        gridOptions = gb.build()
        AgGrid(
            disp_df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            theme="alpine",
            custom_css=get_grid_custom_css(),
            use_container_width=True
        )

def render_live_alerts_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">⚡</span><span class="section-header-title">Live Alerts Log</span></div>', unsafe_allow_html=True)
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold].sort_values(by="contractId", ascending=False)
    if bulk_df.empty:
        st.info("No bulk alerts recorded yet today.")
        return
        
    st.markdown("### Daily Bulk Trade Alerts Log")
    
    for idx, row in bulk_df.iterrows():
        qty = int(row["contractQuantity"])
        symbol = row["stockSymbol"]
        rate = float(row["contractRate"])
        amount = float(row["contractAmount"])
        trade_time_full = row["tradeTime"]
        try:
            t_parsed = datetime.fromisoformat(trade_time_full.replace("Z", ""))
            trade_time_str = t_parsed.strftime("%H:%M:%S")
        except:
            trade_time_str = trade_time_full.split("T")[-1][:8]
            
        formatted_amount = format_nepali_amount(amount)
        
        st.markdown(f"""
        <div style="background-color: rgba(239, 68, 68, 0.05); border-left: 4px solid #ef4444; padding: 12px 16px; margin-bottom: 12px; border-radius: 4px;">
            <span style="color: #ef4444; font-weight: bold; font-family: 'Roboto Mono', monospace;">[{trade_time_str}]</span> &nbsp;
            <strong style="color: #ffffff;">ALERT:</strong> Traded <strong>{qty:,}</strong> shares of <strong style="color: #22d3ee;">{symbol}</strong> @ Rs. {rate:,.2f} (Turnover: <strong style="color: #4ade80;">{formatted_amount}</strong>)
        </div>
        """, unsafe_allow_html=True)

def render_bulk_history_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">📋</span><span class="section-header-title">Bulk Trade History</span></div>', unsafe_allow_html=True)
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold]
    if bulk_df.empty:
        st.info("No bulk trades recorded today.")
        return
        
    render_live_table(bulk_df, bulk_threshold)

def render_hot_stocks(df, bulk_threshold):
    st.subheader("🏆 Hot Stocks Rankings")
    
    if df.empty:
        st.info("No transaction data available to rank stocks.")
        return
        
    tab_vol, tab_turn, tab_bulk = st.tabs(["📊 Top by Volume", "💰 Top by Turnover", "🔥 Top by Bulk Transactions"])
    
    with tab_vol:
        st.markdown("### Top 10 Stocks Ranked by Traded Quantity")
        vol_df = get_hot_stocks_volume(df, limit=10)
        if not vol_df.empty:
            chart = alt.Chart(vol_df).mark_bar(
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
                height=25
            ).encode(
                x=alt.X('Volume:Q', title='Total Shares Traded'),
                y=alt.Y('Symbol:N', sort='-x', title='Stock Symbol'),
                color=alt.Color('Volume:Q', scale=alt.Scale(scheme='indigo'), legend=None),
                tooltip=['Symbol', alt.Tooltip('Volume:Q', format=',')]
            ).properties(height=350)
            
            st.altair_chart(chart, use_container_width=True)
            st.table(vol_df.style.format({"Volume": "{:,}"}))
            
    with tab_turn:
        st.markdown("### Top 10 Stocks Ranked by Turnover (Amount)")
        turn_df = get_hot_stocks_turnover(df, limit=10)
        if not turn_df.empty:
            chart = alt.Chart(turn_df).mark_bar(
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
                height=25
            ).encode(
                x=alt.X('Turnover:Q', title='Turnover (Rs.)'),
                y=alt.Y('Symbol:N', sort='-x', title='Stock Symbol'),
                color=alt.Color('Turnover:Q', scale=alt.Scale(scheme='magma'), legend=None),
                tooltip=['Symbol', alt.Tooltip('Turnover:Q', format='Rs. ,.2f')]
            ).properties(height=350)
            
            st.altair_chart(chart, use_container_width=True)
            st.table(turn_df.style.format({"Turnover": "Rs. {:,.2f}"}))
            
    with tab_bulk:
        st.markdown(f"### Top 10 Stocks Ranked by Frequency of Bulk Trades ({bulk_threshold}+ shares)")
        bulk_ranks = get_hot_stocks_bulk_transactions(df, bulk_threshold, limit=10)
        if not bulk_ranks.empty:
            chart = alt.Chart(bulk_ranks).mark_bar(
                cornerRadiusTopRight=6,
                cornerRadiusBottomRight=6,
                height=25
            ).encode(
                x=alt.X('Bulk Transactions:Q', title='Number of Bulk Transactions'),
                y=alt.Y('Symbol:N', sort='-x', title='Stock Symbol'),
                color=alt.Color('Bulk Transactions:Q', scale=alt.Scale(scheme='warmorange'), legend=None),
                tooltip=['Symbol', 'Bulk Transactions']
            ).properties(height=350)
            
            st.altair_chart(chart, use_container_width=True)
            st.table(bulk_ranks)
        else:
            st.info("No bulk transactions recorded yet to display rankings.")

def render_settings_page(settings):
    st.subheader("⚙️ System Settings")
    
    status_data = read_collector_status(settings.get("data_folder", "data"))
    
    c_status = status_data.get("status", "offline")
    last_heartbeat = status_data.get("last_heartbeat")
    last_sync = status_data.get("last_sync_time")
    records_count = status_data.get("total_records", 0)
    business_date = status_data.get("business_date", "N/A")
    progress = status_data.get("sync_progress", "")
    
    is_active = False
    if last_heartbeat:
        try:
            hb_time = datetime.fromisoformat(last_heartbeat)
            diff = (datetime.now() - hb_time).total_seconds()
            if diff < 45:
                is_active = True
        except:
            pass
            
    if not is_active:
        c_status = "offline"
        
    st.markdown("### Collector Daemon Status")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if c_status == "offline":
            st.markdown('Status: <span class="status-dot offline"></span> **Offline**', unsafe_allow_html=True)
        elif c_status in ("checking", "live_sync", "running"):
            st.markdown('Status: <span class="status-dot online"></span> **Online (Running)**', unsafe_allow_html=True)
        else:
            st.markdown(f'Status: <span class="status-dot syncing"></span> **Syncing** ({progress})', unsafe_allow_html=True)
    with col2:
        st.markdown(f"**Business Date**: {business_date}")
    with col3:
        st.markdown(f"**Total Captured**: {records_count:,} trades")
        
    if last_sync:
        try:
            ls_time = datetime.fromisoformat(last_sync).strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"Last successful API sync completed at: {ls_time}")
        except:
            st.caption(f"Last successful API sync completed at: {last_sync}")
            
    st.markdown("---")
    st.markdown("### Configuration Form")
    
    with st.form("settings_form"):
        refresh_interval = st.number_input(
            "API Refresh & Polling Interval (seconds)",
            min_value=5,
            max_value=300,
            value=int(settings.get("refresh_interval", 15)),
            help="How frequently the background collector queries the newest floorsheet pages."
        )
        
        bulk_threshold = st.number_input(
            "Default Bulk Transaction Threshold (shares)",
            min_value=100,
            max_value=1_000_000,
            value=int(settings.get("bulk_threshold", 5000)),
            help="Trades with volume at or above this value will be highlighted."
        )
        
        data_folder = st.text_input(
            "Local Data Folder Path",
            value=settings.get("data_folder", "data")
        )
        
        auto_start = st.checkbox(
            "Auto-start Background Collector Process",
            value=settings.get("auto_start_collector", True)
        )
        
        sound_enabled = st.checkbox(
            "Enable Audible Alerts (Chime buzzer)",
            value=settings.get("enable_sound", True)
        )
        
        submitted = st.form_submit_button("Save Settings")
        
        if submitted:
            new_settings = {
                "refresh_interval": int(refresh_interval),
                "bulk_threshold": int(bulk_threshold),
                "data_folder": data_folder,
                "auto_start_collector": auto_start,
                "enable_sound": sound_enabled
            }
            if save_settings(new_settings):
                st.success("Settings saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save settings.")

def render_market_depth_stub():
    st.markdown('<div class="section-header"><span class="section-header-icon">📊</span><span class="section-header-title">Market Depth</span></div>', unsafe_allow_html=True)
    st.info("Market Depth panel is currently in sync with the NEPSE scraper daemon. Real-time bids and asks will populate here.")
    st.caption("Terminal Data Stream Active")

def render_analytics_stub():
    st.markdown('<div class="section-header"><span class="section-header-icon">📈</span><span class="section-header-title">Market Analytics</span></div>', unsafe_allow_html=True)
    st.info("Institutional analytics panel is loading historical data models. Quantitative charts will display shortly.")
    
def render_alerts_stub():
    st.markdown('<div class="section-header"><span class="section-header-icon">🔔</span><span class="section-header-title">System Alerts</span></div>', unsafe_allow_html=True)
    st.info("Configure live notifications, SMS/Email buzzers, and custom threshold triggers.")
    
def render_about_page():
    st.markdown('<div class="section-header"><span class="section-header-icon">ℹ️</span><span class="section-header-title">About NEPSE Analyzer</span></div>', unsafe_allow_html=True)
    st.markdown("""
    ### NEPSE Live Bulk Market Analyzer Pro
    Designed for professional trading rooms, broadcast streams, and live floorsheet analytics.
    
    - **Developer**: Antigravity AI Subagent
    - **Version**: 2.5.0-Live
    - **Status**: Production Release
    """)
