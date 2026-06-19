import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# Robust import for streamlit-aggrid across versions
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
try:
    from st_aggrid import JsCode
except ImportError:
    from st_aggrid.shared import JsCode

from dashboard.styles import get_grid_custom_css, get_grid_tv_css

# -------------------------------------------------------------
# Formatting Utilities
# -------------------------------------------------------------
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
    
    if "ETF" in symbol or "ETF" in name:
        return "ETF"
    if "MUTUAL FUND" in name or "FUND" in name or "YOJANA" in name or "SCHEME" in name or symbol.endswith("MF"):
        return "Mutual Fund"
    if "DEBENTURE" in name or "BOND" in name or "%" in name or (symbol.endswith("D") and len(symbol) > 4) or any(symbol.endswith(f"D{yr}") for yr in range(70, 100)):
        return "Debenture"
    if "PREFERENCE" in name or "PREF" in name or symbol.endswith("P") or symbol.endswith("PS"):
        return "Preference Share"
    if "RIGHT" in name or "RIGHTS" in name or symbol.endswith("R"):
        return "Rights Share"
    return "Equity"

# -------------------------------------------------------------
# AgGrid Cell Renderers (JsCode)
# -------------------------------------------------------------
symbol_renderer = JsCode("""
class SymbolRenderer {
    init(params) {
        this.eGui = document.createElement('span');
        if (params.value != null) {
            this.eGui.innerHTML = '<strong style="color: #A78BFA; font-weight: 700; cursor: pointer;">' + params.value + '</strong>';
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
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(109, 40, 217, 0.2); border: 1px solid #6D28D9; color: #A78BFA;">Mutual Fund</span>';
            } else if (val === 'Equity') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(59, 130, 246, 0.2); border: 1px solid #3B82F6; color: #93C5FD;">Equity</span>';
            } else if (val === 'Debenture') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(245, 158, 11, 0.2); border: 1px solid #D97706; color: #FBBF24;">Debenture</span>';
            } else if (val === 'ETF') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(6, 182, 212, 0.2); border: 1px solid #0891B2; color: #22D3EE;">ETF</span>';
            } else if (val === 'Rights Share' || val === 'Rights') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(16, 185, 129, 0.2); border: 1px solid #059669; color: #34D399;">Rights</span>';
            } else if (val === 'Preference Share') {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(225, 29, 72, 0.2); border: 1px solid #E11D48; color: #FDA4AF;">Pref. Share</span>';
            } else {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(148, 163, 184, 0.2); border: 1px solid #475569; color: #CBD5E1;">' + val + '</span>';
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
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #FCA5A5;">Bulk</span>';
            } else {
                this.eGui.innerHTML = '<span style="display: inline-block; padding: 2px 8px; font-size: 10px; font-weight: 700; border-radius: 12px; text-transform: uppercase; background: rgba(71, 85, 105, 0.2); border: 1px solid #475569; color: #94A3B8;">Normal</span>';
            }
        }
    }
    getGui() {
        return this.eGui;
    }
}
""")

qty_formatter = JsCode("function(params) { return params.value == null ? '' : Number(params.value).toLocaleString('en-US'); }")
rate_formatter = JsCode("function(params) { return params.value == null ? '' : 'Rs. ' + Number(params.value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }")
amount_formatter = JsCode("function(params) { return params.value == null ? '' : 'Rs. ' + Number(params.value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }")

qty_cellstyle_jscode = JsCode("""
function(params) {
    var qty = params.value;
    if (qty == null) return {};
    if (qty >= 100000) {
        return { 'color': '#EF4444', 'fontWeight': '800' };
    } else if (qty >= 50000) {
        return { 'color': '#F87171', 'fontWeight': '700' };
    } else if (qty >= 25000) {
        return { 'color': '#F59E0B', 'fontWeight': '700' };
    } else if (qty >= 10000) {
        return { 'color': '#FBBF24', 'fontWeight': '600' };
    } else {
        return { 'color': '#FFFFFF' };
    }
}
""")

def configure_grid_columns(gb, table_cols):
    if "Symbol" in table_cols:
        gb.configure_column("Symbol", cellRenderer=symbol_renderer)
    if "Instrument Type" in table_cols:
        gb.configure_column("Instrument Type", cellRenderer=instrument_renderer)
    if "Trade Type" in table_cols:
        gb.configure_column("Trade Type", cellRenderer=trade_type_renderer)
    if "Quantity" in table_cols:
        gb.configure_column("Quantity", valueFormatter=qty_formatter, cellStyle=qty_cellstyle_jscode)
    if "Rate" in table_cols:
        gb.configure_column("Rate", valueFormatter=rate_formatter, cellStyle={"color": "#10B981"})
    if "Amount" in table_cols:
        gb.configure_column("Amount", valueFormatter=amount_formatter, cellStyle={"color": "#FBBF24"})
    if "Contract ID" in table_cols:
        gb.configure_column("Contract ID", cellStyle={"color": "#64748B", "fontFamily": "Roboto Mono"})
    if "Trade Time" in table_cols:
        gb.configure_column("Trade Time", cellStyle={"color": "#E2E8F0", "fontFamily": "Roboto Mono"})
    if "Company" in table_cols:
        gb.configure_column("Company", cellStyle={"color": "#E2E8F0"})

# -------------------------------------------------------------
# Base Rendering Functions
# -------------------------------------------------------------
def render_summary_cards(df, bulk_threshold):
    """
    Renders 4 premium summary metrics cards:
    - Total Bulk Volume (shares)
    - Active Symbols (unique symbols traded today)
    - Top Gainer by Bulk Activity (symbol with highest bulk transaction amount today)
    - Largest Trade Today (single transaction with highest quantity/amount)
    """
    # Calculate stats
    bulk_df = df[df["contractQuantity"] >= bulk_threshold] if not df.empty else pd.DataFrame()
    total_bulk_vol = bulk_df["contractQuantity"].sum() if not bulk_df.empty else 0
    active_syms = df["stockSymbol"].nunique() if not df.empty else 0
    
    # Top bulk activity stock
    if not bulk_df.empty:
        bulk_sums = bulk_df.groupby("stockSymbol")["contractAmount"].sum()
        top_bulk_sym = bulk_sums.idxmax()
        top_bulk_val = bulk_sums.max()
        top_gainer_bulk = f"{top_bulk_sym} ({format_nepali_amount(top_bulk_val)})"
    else:
        top_gainer_bulk = "N/A"
        
    # Largest trade
    if not df.empty:
        idx_max = df["contractAmount"].idxmax()
        max_trade_sym = df.loc[idx_max, "stockSymbol"]
        max_trade_qty = int(df.loc[idx_max, "contractQuantity"])
        max_trade_amt = float(df.loc[idx_max, "contractAmount"])
        largest_trade_today = f"{max_trade_sym} ({max_trade_qty:,} sh / {format_nepali_amount(max_trade_amt)})"
    else:
        largest_trade_today = "N/A"
        
    cards_html = f"""
    <div class="dashboard-kpi-grid">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Total Bulk Volume</span>
                <span class="kpi-icon">📊</span>
            </div>
            <div class="kpi-value">{total_bulk_vol:,}</div>
            <span class="kpi-sub">Shares Traded (>{bulk_threshold:,})</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Active Symbols</span>
                <span class="kpi-icon">⚡</span>
            </div>
            <div class="kpi-value">{active_syms}</div>
            <span class="kpi-sub">Unique Stocks Traded Today</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Top Bulk Activity</span>
                <span class="kpi-icon">🔥</span>
            </div>
            <div class="kpi-value" style="font-size: 20px !important; margin: 18px 0 8px 0; color: #10B981 !important;">{top_gainer_bulk}</div>
            <span class="kpi-sub">Highest Bulk Turnover Today</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Largest Trade</span>
                <span class="kpi-icon">💎</span>
            </div>
            <div class="kpi-value" style="font-size: 16px !important; margin: 20px 0 10px 0; color: #F59E0B !important;">{largest_trade_today}</div>
            <span class="kpi-sub">Single Largest Execution Today</span>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)

def play_alert_sound():
    sound_html = """
    <script>
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const ctx = new AudioContext();
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(880, ctx.currentTime);
            gain1.gain.setValueAtTime(0.05, ctx.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            
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
    bulk_trades = df[df["contractQuantity"] >= bulk_threshold] if not df.empty else pd.DataFrame()
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
    <div class="live-bulk-alert-container">
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 18px; color: #A78BFA;">🚨</span>
                <span style="color: #ffffff; font-family: 'Inter', sans-serif; font-size: 14px;">
                    <strong>LIVE ALERT:</strong> Traded <strong>{qty:,}</strong> shares of <strong style="color: #A78BFA;">{symbol}</strong> at <strong>Rs. {rate:,.2f}</strong> (Turnover: <strong>{formatted_amount}</strong>) at {trade_time_str}.
                </span>
            </div>
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
        <div class="filter-title">🔎 Advanced Query Filters</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1.5, 2.5, 2.5, 1.8, 1.7])
        with col1:
            bulk_qty_opt = st.selectbox(
                "Filter by Min Quantity",
                options=["All", "5,000+", "10,000+", "25,000+", "50,000+", "100,000+"],
                index=1
            )
        with col2:
            all_symbols = sorted(df["stockSymbol"].unique()) if not df.empty else []
            selected_symbols = st.multiselect(
                "Filter by Stock Symbol",
                options=all_symbols,
                default=[]
            )
        with col3:
            st.markdown("<div style='font-size: 12px; font-weight: 600; color: #94a3b8; margin-bottom: 4px;'>Trading Time Range</div>", unsafe_allow_html=True)
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                start_time_str = st.text_input("Start", value="11:00", label_visibility="collapsed")
            with t_col2:
                end_time_str = st.text_input("End", value="15:00", label_visibility="collapsed")
        with col4:
            instr_opt = st.selectbox(
                "Instrument Category",
                options=["All", "Equity", "Mutual Fund", "Preference Share", "Debenture", "Rights Share", "ETF"],
                index=0
            )
        with col5:
            turnover_opt = st.selectbox(
                "Turnover Range",
                options=["All", "Below 1 Lakh", "1 Lakh – 5 Lakh", "5 Lakh – 10 Lakh", "10 Lakh – 50 Lakh", "50 Lakh – 1 Crore", "Above 1 Crore"],
                index=0
            )

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

def render_live_table(df, bulk_threshold):
    if df.empty:
        st.info("No trades found matching current filter query.")
        return
        
    display_df = df.copy().sort_values(by="contractId", ascending=False)
    
    col_sel, col_dl = st.columns([8.2, 1.8])
    with col_sel:
        row_count = st.selectbox("Show rows", options=[25, 50, 100, 200, 500], index=1, key="table_row_count", label_visibility="collapsed")
    with col_dl:
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export CSV Data",
            data=csv_data,
            file_name=f"TradeNepse_floorsheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
    
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_default_column(resizable=True, filterable=True, sortable=True, editable=False)
    configure_grid_columns(gb, table_df.columns)
        
    gb.configure_grid_options(
        rowHeight=44,
        headerHeight=46,
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
    Main Live Dashboard viewport layout.
    """
    # 1. Alert Banner
    render_alert_banner(df, bulk_threshold, enable_sound)
    
    # 2. Advanced Horizontal Filters
    f_df = render_filter_bar(df, bulk_threshold)
    
    # 3. KPI Summary cards
    st.markdown('<div class="section-header"><span class="section-header-icon">📊</span><span class="section-header-title">Market Intelligence Metrics</span></div>', unsafe_allow_html=True)
    render_summary_cards(f_df, bulk_threshold)
    
    # 4. Live Table Feed
    live_feed_header = """
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1E293B; margin-top: 25px; margin-bottom: 15px; padding-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px; color: #8B5CF6;">⚡</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 800; color: #ffffff; text-transform: uppercase;">Floorsheet Activity Feed</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; font-size: 13px; color: #64748b;">
            <span style="color: #10B981; font-weight: bold; font-family: 'Inter', sans-serif;">● Live Stream Active</span>
        </div>
    </div>
    """
    st.markdown(live_feed_header, unsafe_allow_html=True)

    render_live_table(f_df, bulk_threshold)
        


# -------------------------------------------------------------
# TV Mode View (Optimized for Large screens)
# -------------------------------------------------------------
def render_tv_mode(df, bulk_threshold, refresh_interval, enable_sound):
    """
    OBS/Big TV optimized viewport.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    header_html = f"""
    <div class="tv-header-container">
        <div class="tv-header-title">📊 TradeNepse Live Terminal</div>
        <div class="tv-header-time">{now_str}</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # TV Alert Banner
    bulk_trades = df[df["contractQuantity"] >= bulk_threshold] if not df.empty else pd.DataFrame()
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
            <div class="tv-alert-header">🚨 BLOCK TRADE ENGAGED</div>
            <div class="tv-alert-grid">
                <div class="alert-item">
                    <span class="alert-label" style="display:block; font-size:10px; color:#A78BFA;">Symbol</span>
                    <span class="tv-alert-val sym">{symbol}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label" style="display:block; font-size:10px; color:#A78BFA;">Quantity</span>
                    <span class="tv-alert-val qty">{qty:,}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label" style="display:block; font-size:10px; color:#A78BFA;">Rate</span>
                    <span class="tv-alert-val">Rs. {rate:,.2f}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label" style="display:block; font-size:10px; color:#A78BFA;">Turnover</span>
                    <span class="tv-alert-val val">{formatted_amount}</span>
                </div>
                <div class="alert-item">
                    <span class="alert-label" style="display:block; font-size:10px; color:#A78BFA;">Execution Time</span>
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
                
    # Giant TV KPI Cards
    active_syms = df["stockSymbol"].nunique() if not df.empty else 0
    total_bulk_vol = bulk_trades["contractQuantity"].sum() if not bulk_trades.empty else 0
    
    if not bulk_trades.empty:
        bulk_sums = bulk_trades.groupby("stockSymbol")["contractAmount"].sum()
        top_bulk_sym = bulk_sums.idxmax()
        top_bulk_val = bulk_sums.max()
        top_gainer_bulk = f"{top_bulk_sym} ({format_nepali_amount(top_bulk_val)})"
    else:
        top_gainer_bulk = "N/A"
        
    if not df.empty:
        idx_max = df["contractAmount"].idxmax()
        max_trade_sym = df.loc[idx_max, "stockSymbol"]
        max_trade_qty = int(df.loc[idx_max, "contractQuantity"])
        largest_trade_today = f"{max_trade_sym} ({max_trade_qty:,} sh)"
    else:
        largest_trade_today = "N/A"
        
    tv_cards_html = f"""
    <div class="tv-grid">
        <div class="tv-card">
            <div class="tv-label">Total Bulk Volume</div>
            <div class="tv-value">{total_bulk_vol:,}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Active Symbols</div>
            <div class="tv-value">{active_syms}</div>
        </div>
        <div class="tv-card accent">
            <div class="tv-label">Top Bulk Activity</div>
            <div class="tv-value" style="color: #34D399; font-size: 24px;">{top_gainer_bulk}</div>
        </div>
        <div class="tv-card">
            <div class="tv-label">Largest Trade</div>
            <div class="tv-value" style="color: #ffd60a; font-size: 24px;">{largest_trade_today}</div>
        </div>
    </div>
    """
    st.markdown(tv_cards_html, unsafe_allow_html=True)
    
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
        rowHeight=54,
        headerHeight=54,
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
    
    st.markdown('<div class="tv-exit-container">', unsafe_allow_html=True)
    if st.button("Exit TV Terminal"):
        st.session_state.tv_mode = False
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# Hot Stocks Page View
# -------------------------------------------------------------
def render_hot_bulk_stocks_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">🔥</span><span class="section-header-title">Hot Stocks Rankings (Bulk activity)</span></div>', unsafe_allow_html=True)
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold] if not df.empty else pd.DataFrame()
    if bulk_df.empty:
        st.info("No bulk transactions captured yet today. Rankings will populate as trades occur.")
        return
        
    # Compile statistics
    grouped = bulk_df.groupby("stockSymbol").agg(
        total_qty=("contractQuantity", "sum"),
        total_turnover=("contractAmount", "sum"),
        trades_count=("contractId", "count"),
        largest_trade=("contractAmount", "max")
    ).reset_index()
    
    # Calculate Activity Score (trades_count weight + turnover log weight)
    grouped["activity_score"] = (grouped["trades_count"] * 5) + (grouped["total_turnover"] / 100_000)
    grouped["activity_score"] = grouped["activity_score"].round(1)
    
    # Top 3 Highlighting Metrics
    top_turnover_row = grouped.sort_values(by="total_turnover", ascending=False).iloc[0]
    top_trades_row = grouped.sort_values(by="trades_count", ascending=False).iloc[0]
    top_score_row = grouped.sort_values(by="activity_score", ascending=False).iloc[0]
    
    top_cards_html = f"""
    <div class="dashboard-kpi-grid">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Highest Turnover Stock</span>
                <span class="kpi-icon">💰</span>
            </div>
            <div class="kpi-value" style="font-size: 20px !important; margin: 18px 0 8px 0; color: #10B981 !important;">{top_turnover_row['stockSymbol']}</div>
            <span class="kpi-sub">Total Turnover: {format_nepali_amount(top_turnover_row['total_turnover'])}</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Most Bulk Transactions</span>
                <span class="kpi-icon">🔄</span>
            </div>
            <div class="kpi-value" style="font-size: 20px !important; margin: 18px 0 8px 0; color: #3B82F6 !important;">{top_trades_row['stockSymbol']}</div>
            <span class="kpi-sub">Bulk Trades Count: {top_trades_row['trades_count']:,}</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Highest Activity Score</span>
                <span class="kpi-icon">⚡</span>
            </div>
            <div class="kpi-value" style="font-size: 20px !important; margin: 18px 0 8px 0; color: #F59E0B !important;">{top_score_row['stockSymbol']}</div>
            <span class="kpi-sub">Activity Score: {top_score_row['activity_score']} pts</span>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-label">Active Hot Stocks</span>
                <span class="kpi-icon">📈</span>
            </div>
            <div class="kpi-value">{len(grouped)}</div>
            <span class="kpi-sub">Total Symbols with Bulk Trade Activity</span>
        </div>
    </div>
    """
    st.markdown(top_cards_html, unsafe_allow_html=True)
    
    # Sorting controls & options
    st.markdown("#### Hot Stocks Leaderboard")
    sort_by_field = st.selectbox("Rank By", options=["Activity Score", "Bulk Turnover", "Bulk Quantity", "Number Of Bulk Trades"], index=0)
    
    map_sort_fields = {
        "Activity Score": "activity_score",
        "Bulk Turnover": "total_turnover",
        "Bulk Quantity": "total_qty",
        "Number Of Bulk Trades": "trades_count"
    }
    
    sorted_df = grouped.sort_values(by=map_sort_fields[sort_by_field], ascending=False).reset_index(drop=True)
    sorted_df.insert(0, "Rank", sorted_df.index + 1)
    
    sorted_df = sorted_df.rename(columns={
        "stockSymbol": "Symbol",
        "activity_score": "Activity Score",
        "total_qty": "Bulk Quantity",
        "total_turnover": "Bulk Turnover",
        "trades_count": "Number Of Bulk Trades",
        "largest_trade": "Largest Trade"
    })
    
    table_view_df = sorted_df[["Rank", "Symbol", "Activity Score", "Bulk Quantity", "Bulk Turnover", "Number Of Bulk Trades", "Largest Trade"]]
    
    gb = GridOptionsBuilder.from_dataframe(table_view_df)
    gb.configure_default_column(resizable=True, sortable=True)
    gb.configure_column("Rank", width=80)
    gb.configure_column("Symbol", cellRenderer=symbol_renderer)
    gb.configure_column("Activity Score", cellStyle={"color": "#F59E0B", "fontWeight": "bold"})
    gb.configure_column("Bulk Quantity", valueFormatter=qty_formatter)
    gb.configure_column("Bulk Turnover", valueFormatter=amount_formatter)
    gb.configure_column("Number Of Bulk Trades", valueFormatter=qty_formatter)
    gb.configure_column("Largest Trade", valueFormatter=amount_formatter)
    
    gridOptions = gb.build()
    
    AgGrid(
        table_view_df,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        theme="alpine",
        custom_css=get_grid_custom_css(),
        use_container_width=True
    )

# -------------------------------------------------------------
# Largest Trades Page View
# -------------------------------------------------------------
def render_largest_trades_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">💰</span><span class="section-header-title">Largest Trades Board</span></div>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("No transaction data available yet today.")
        return
        
    col_limit, col_filt = st.columns([3, 7])
    with col_limit:
        limit = st.selectbox("Show Top Trades", options=[25, 50, 100, 250], index=1)
    with col_filt:
        min_qty_filter = st.slider("Filter by Minimum Share Quantity", min_value=1000, max_value=100000, value=10000, step=1000)
        
    filtered_df = df[df["contractQuantity"] >= min_qty_filter]
    if filtered_df.empty:
        st.info(f"No trades found with quantity >= {min_qty_filter:,}.")
        return
        
    large_df = filtered_df.sort_values(by="contractAmount", ascending=False).head(limit)
    
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
        rowHeight=44,
        headerHeight=46,
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

# -------------------------------------------------------------
# Symbol Analytics Page View
# -------------------------------------------------------------
def render_symbol_analytics_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">📈</span><span class="section-header-title">Symbol Intelligence & Analytics</span></div>', unsafe_allow_html=True)
    
    if df.empty:
        st.info("No transaction data available yet today.")
        return
        
    all_symbols = sorted(df["stockSymbol"].unique())
    selected_symbol = st.selectbox("Search Stock Symbol", options=all_symbols)
    
    symbol_df = df[df["stockSymbol"] == selected_symbol].copy()
    bulk_symbol_df = symbol_df[symbol_df["contractQuantity"] >= bulk_threshold]
    
    # Basic Stats
    total_trades = len(symbol_df)
    total_bulk_trades = len(bulk_symbol_df)
    total_qty = symbol_df["contractQuantity"].sum()
    bulk_qty = bulk_symbol_df["contractQuantity"].sum()
    total_turnover = symbol_df["contractAmount"].sum()
    bulk_turnover = bulk_symbol_df["contractAmount"].sum()
    avg_price = symbol_df["contractRate"].mean() if total_trades > 0 else 0
    
    st.markdown(f"### Analysis for symbol: **{selected_symbol}**")
    
    # Stats Layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", f"{total_trades:,}")
        st.metric("Bulk Trades Count", f"{total_bulk_trades:,}")
    with col2:
        st.metric("Total Share Volume", f"{total_qty:,}")
        ratio_qty = (bulk_qty/total_qty*100) if total_qty > 0 else 0
        st.metric("Bulk Share Volume", f"{bulk_qty:,} ({ratio_qty:.1f}%)")
    with col3:
        st.metric("Total Turnover", format_nepali_amount(total_turnover))
        ratio_turn = (bulk_turnover/total_turnover*100) if total_turnover > 0 else 0
        st.metric("Bulk Turnover", format_nepali_amount(bulk_turnover))
    with col4:
        st.metric("Avg Trade Price", f"Rs. {avg_price:,.2f}")
        bulk_avg = bulk_symbol_df["contractRate"].mean() if total_bulk_trades > 0 else 0
        st.metric("Avg Bulk Price", f"Rs. {bulk_avg:,.2f}" if bulk_avg > 0 else "N/A")

    # Tick-Test Buy/Sell Classification Proxy
    if total_trades > 1:
        symbol_df = symbol_df.sort_values(by="contractId").copy()
        rates = symbol_df["contractRate"].values
        directions = ["Neutral"]
        last_dir = "Neutral"
        for i in range(1, len(rates)):
            diff = rates[i] - rates[i-1]
            if diff > 0:
                directions.append("Buy")
                last_dir = "Buy"
            elif diff < 0:
                directions.append("Sell")
                last_dir = "Sell"
            else:
                directions.append(last_dir)
        symbol_df["TickDirection"] = directions
        
        buy_vol = symbol_df[symbol_df["TickDirection"] == "Buy"]["contractQuantity"].sum()
        sell_vol = symbol_df[symbol_df["TickDirection"] == "Sell"]["contractQuantity"].sum()
        total_dir_vol = buy_vol + sell_vol
        
        if total_dir_vol > 0:
            buy_percent = (buy_vol / total_dir_vol) * 100
            sell_percent = (sell_vol / total_dir_vol) * 100
        else:
            buy_percent, sell_percent = 50.0, 50.0
            
        st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: 25px;">
            <h5 style="color: white; margin-bottom: 8px; font-family: 'Outfit';">Intraday Buy/Sell Volume Pressure (Tick-Test Proxy)</h5>
            <div style="display: flex; height: 26px; border-radius: 8px; overflow: hidden; width: 100%; border: 1px solid #1E293B;">
                <div style="background-color: #059669; width: {buy_percent}%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px;">
                    BUY INITIATED: {buy_percent:.1f}% ({buy_vol:,} shares)
                </div>
                <div style="background-color: #DC2626; width: {sell_percent}%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px;">
                    SELL INITIATED: {sell_percent:.1f}% ({sell_vol:,} shares)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # Volume Trend Chart
    st.markdown("#### Intraday Share Volume Trend")
    symbol_df["ParsedTime"] = pd.to_datetime(symbol_df["tradeTime"].str.replace("Z", ""), errors="coerce")
    symbol_df = symbol_df.dropna(subset=["ParsedTime"]).sort_values("ParsedTime")
    
    if not symbol_df.empty:
        chart = alt.Chart(symbol_df).mark_bar(color="#7C3AED", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("ParsedTime:T", title="Trade Time"),
            y=alt.Y("contractQuantity:Q", title="Quantity (Shares)"),
            color=alt.condition(
                alt.datum.contractQuantity >= bulk_threshold,
                alt.value("#EC4899"), # Pink for bulk trades
                alt.value("#6366F1")  # Blue-violet for normal trades
            ),
            tooltip=[
                alt.Tooltip("tradeTime:N", title="Time"),
                alt.Tooltip("contractQuantity:Q", title="Quantity"),
                alt.Tooltip("contractRate:Q", title="Price"),
                alt.Tooltip("contractAmount:Q", title="Turnover")
            ]
        ).properties(
            height=300
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        st.caption("Pink bars signify transactions exceeding the bulk volume threshold.")
    else:
        st.info("No time series data parsed to render charts.")

    # Historical Bulk Trades insights list
    if not bulk_symbol_df.empty:
        st.markdown("#### Historical Intraday Bulk Transactions")
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
            rowHeight=44,
            headerHeight=46,
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

# -------------------------------------------------------------
# Live Alerts Log Page View
# -------------------------------------------------------------
def render_live_alerts_page(df, bulk_threshold):
    st.markdown('<div class="section-header"><span class="section-header-icon">🚨</span><span class="section-header-title">Live Intel & Block Alerts</span></div>', unsafe_allow_html=True)
    
    bulk_df = df[df["contractQuantity"] >= bulk_threshold].copy() if not df.empty else pd.DataFrame()
    if bulk_df.empty:
        st.info("No bulk alerts logged yet today. Real-time entries will compile automatically.")
        return
        
    st.markdown("### Today's Cumulative Bulk Alert Log")
    
    # Sort descending to show newest alerts first
    bulk_df = bulk_df.sort_values(by="contractId", ascending=False)
    
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
        
        # Color coding by severity
        if qty >= 50000:
            border_color = "#DC2626"
            bg_color = "rgba(220, 38, 38, 0.04)"
            badge_text = "Critical Block Trade"
            badge_color = "#DC2626"
        elif qty >= 25000:
            border_color = "#D97706"
            bg_color = "rgba(217, 119, 6, 0.04)"
            badge_text = "Large Bulk Trade"
            badge_color = "#D97706"
        else:
            border_color = "#2563EB"
            bg_color = "rgba(37, 99, 235, 0.04)"
            badge_text = "Bulk Trade"
            badge_color = "#2563EB"
            
        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-left: 6px solid {border_color}; padding: 14px 18px; margin-bottom: 12px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">
                    {badge_text}
                </span>
                <span style="color: #64748B; font-family: 'Roboto Mono', monospace; font-size: 11px; font-weight: bold;">
                    {trade_time_str}
                </span>
            </div>
            <div style="color: #E2E8F0; font-size: 14px; font-family: 'Inter', sans-serif;">
                Traded <strong style="color: #FFFFFF; font-size: 15px;">{qty:,}</strong> shares of <strong style="color: #A78BFA; font-size: 15px;">{symbol}</strong> @ Rs. {rate:,.2f} (Turnover: <strong style="color: #34D399;">{formatted_amount}</strong>)
            </div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# Coming Soon Placeholder Page View
# -------------------------------------------------------------
def render_coming_soon_page(page_name, page_icon):
    st.markdown(f'<div class="section-header"><span class="section-header-icon">{page_icon}</span><span class="section-header-title">{page_name}</span></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #0B0F19 100%); border: 1px solid #1E293B; border-radius: 12px; padding: 50px 30px; text-align: center; margin-top: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="font-size: 64px; margin-bottom: 20px; filter: drop-shadow(0 0 12px #6D28D9);">{page_icon}</div>
        <h3 style="color: white; margin-bottom: 10px; font-family: 'Outfit'; font-weight: 800;">{page_name} Workspace</h3>
        <p style="color: #94A3B8; font-size: 14px; max-width: 500px; margin: 0 auto 25px auto; font-family: 'Inter'; line-height: 1.5;">
            We are designing a high-fidelity quantitative analysis workspace for institutional NEPSE traders. This feature is currently in active development.
        </p>
        <div style="display: inline-block; background-color: rgba(109, 40, 217, 0.1); border: 1px solid #6D28D9; border-radius: 20px; padding: 6px 18px; font-size: 12px; font-weight: 700; color: #A78BFA; text-transform: uppercase; letter-spacing: 1.5px; font-family: 'Inter';">
            ⚡ Coming Soon to TradeNepse
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_admin_loot_workspace(settings):
    from settings.config import save_settings
    from analytics.schedule import get_market_status, get_next_market_open, get_next_market_close
    import pytz
    
    # -------------------------------------------------------------
    # ⚙️ Diagnostics Monitor
    # -------------------------------------------------------------
    st.markdown("### ⚙️ Diagnostics")
    
    tz_name = settings.get("timezone", "Asia/Kathmandu")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("Asia/Kathmandu")
        
    nepal_now = datetime.now(tz)
    nepal_now_str = nepal_now.strftime("%Y-%m-%d %I:%M:%S %p (%Z)")
    
    status_str = get_market_status()
    
    next_open = get_next_market_open()
    next_open_str = next_open.strftime("%Y-%m-%d %I:%M %p") if next_open else "N/A"
    
    next_close = get_next_market_close()
    next_close_str = next_close.strftime("%Y-%m-%d %I:%M %p") if next_close else "N/A"
    
    st.markdown(f"""
    <div style="background-color: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Current Nepal Time</div>
                <div style="font-size: 14px; font-weight: 700; color: white; font-family: 'Roboto Mono', monospace;">{nepal_now_str}</div>
            </div>
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Current Market Status</div>
                <div style="font-size: 14px; font-weight: 700; color: {'#10B981' if 'Open' in status_str else '#F59E0B'}; font-family: 'Inter';">{status_str}</div>
            </div>
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Next Market Open Time</div>
                <div style="font-size: 14px; font-weight: 700; color: white; font-family: 'Roboto Mono', monospace;">{next_open_str}</div>
            </div>
            <div>
                <div style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Next Market Close Time</div>
                <div style="font-size: 14px; font-weight: 700; color: white; font-family: 'Roboto Mono', monospace;">{next_close_str}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Two Columns: Left = Schedule Settings, Right = System Controls
    # -------------------------------------------------------------
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### ⚙️ Market Schedule Settings")
        with st.form("admin_market_schedule_form"):
            form_timezone = st.text_input(
                "Timezone Context", 
                value=settings.get("timezone", "Asia/Kathmandu")
            )
            form_open = st.text_input(
                "Market Open Time (24h Format HH:MM)", 
                value=settings.get("market_open", "11:01")
            )
            form_close = st.text_input(
                "Market Close Time (24h Format HH:MM)", 
                value=settings.get("market_close", "15:05")
            )
            
            days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_indices = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            inv_days = {v: k for k, v in days_indices.items()}
            current_days = [inv_days[d] for d in settings.get("trading_days", [0, 1, 2, 3, 4, 6]) if d in inv_days]
            
            form_days = st.multiselect(
                "Configure Trading Session Weekdays",
                options=days_options,
                default=current_days
            )
            
            form_interval = st.number_input(
                "Browser Refresh Frequency (seconds)",
                min_value=5, max_value=300,
                value=int(settings.get("refresh_interval_seconds", settings.get("refresh_interval", 15)))
            )
            
            form_holiday = st.checkbox(
                "Holiday Mode Activated", 
                value=settings.get("holiday_mode", False)
            )
            
            form_pass = st.text_input(
                "Change Admin Password (leave blank to keep current)", 
                type="password"
            )
            
            submit_schedule = st.form_submit_button("Save Market Schedule", type="primary", use_container_width=True)
            
            if submit_schedule:
                new_days_list = [days_indices[d] for d in form_days]
                settings["timezone"] = form_timezone.strip()
                settings["market_open"] = form_open.strip()
                settings["market_close"] = form_close.strip()
                settings["trading_days"] = new_days_list
                settings["refresh_interval"] = int(form_interval)
                settings["refresh_interval_seconds"] = int(form_interval)
                settings["holiday_mode"] = form_holiday
                if form_pass.strip():
                    settings["admin_password"] = form_pass.strip()
                    
                if save_settings(settings):
                    st.success("Market schedule configurations updated successfully!")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to write to settings.json.")

    with col_right:
        st.markdown("### ⚙️ System Controls")
        with st.form("admin_system_controls_form"):
            control_auto_ref = st.checkbox(
                "Enable Auto Refresh", 
                value=settings.get("enable_auto_refresh", True),
                help="Toggle standard browser autorefresh loops."
            )
            control_force_open = st.checkbox(
                "Force Market Open", 
                value=settings.get("force_market_open", False),
                help="Overrides normal schedule checking to force status: OPEN."
            )
            control_force_close = st.checkbox(
                "Force Market Closed", 
                value=settings.get("force_market_closed", False),
                help="Overrides normal schedule checking to force status: CLOSED."
            )
            
            submit_controls = st.form_submit_button("Save System Controls", type="primary", use_container_width=True)
            
            if submit_controls:
                # Basic validation: cannot force both open and closed!
                if control_force_open and control_force_close:
                    st.error("Invalid Configuration: Cannot force market to be Open and Closed simultaneously.")
                else:
                    settings["enable_auto_refresh"] = control_auto_ref
                    settings["force_market_open"] = control_force_open
                    settings["force_market_closed"] = control_force_close
                    
                    if save_settings(settings):
                        st.success("System controls saved successfully!")
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to write controls to settings.json.")
