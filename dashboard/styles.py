def get_custom_css():
    """
    Returns custom CSS for a premium dark mode, trading terminal aesthetics,
    and audited contrast elements for the main dashboard.
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800;900&family=Roboto+Mono:wght@400;500;700&display=swap');
    
    /* Global Styles */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #020617 !important;
        color: #CBD5E1 !important;
        font-size: 16px !important;
    }
    
    /* Header & Titles */
    h1, h2, h3, h4, h5, h6, .stHeader, [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
    }
    
    /* Section Header Custom Component */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 35px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #334155;
    }
    .section-header-icon {
        font-size: 26px;
    }
    .section-header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 22px;
        font-weight: 800;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #334155 !important;
    }
    [data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    
    /* Primary / Accent Buttons */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #8B5CF6 !important;
        border-color: #8B5CF6 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 10px rgba(139, 92, 246, 0.2) !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #a78bfa !important;
        border-color: #a78bfa !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 15px rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Outline / Secondary / Export Buttons */
    div[data-testid="stButton"] button[kind="secondary"], 
    div[data-testid="stDownloadButton"] button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover, 
    div[data-testid="stDownloadButton"] button:hover {
        border-color: #8B5CF6 !important;
        color: #FFFFFF !important;
        background-color: #111827 !important;
        box-shadow: 0 0 8px rgba(139, 92, 246, 0.15) !important;
    }
    
    /* Compact KPI Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 8px;
        margin-bottom: 4px;
    }

    .metric-card {
        background: #111827 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px;
        padding: 10px 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 80px;
    }

    .metric-card:hover {
        transform: translateY(-1px);
        border-color: #8B5CF6 !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2);
    }

    .metric-header {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .metric-icon {
        font-size: 14px;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 5px;
    }

    .metric-label {
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-top: 2px;
    }

    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 24px !important;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.3px;
        margin: 4px 0 1px 0;
    }

    .metric-sub {
        font-size: 9px;
        color: #94A3B8;
        font-family: 'Inter', sans-serif;
    }
        
    /* Live Bulk Alert Banner */
    .live-bulk-alert-container {
        background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%) !important;
        border: 2px solid #EF4444 !important;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 25px;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
        animation: pulse-alert-border 1.5s infinite alternate;
    }
    
    @keyframes pulse-alert-border {
        0% {
            border-color: #991b1b;
            box-shadow: 0 0 8px rgba(185, 28, 28, 0.3);
        }
        100% {
            border-color: #EF4444;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
        }
    }
    
    /* Filter Bar Box */
    .filter-panel {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        padding: 5px 10px;
        margin-bottom: 5px;
    }
    
    .filter-title {
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        font-weight: 500;
        color: #8B5CF6;
        margin-bottom: 0px;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Form Inputs and Select Boxes Overrides to Prevent Low Contrast */
    div[data-testid="stSelectbox"] label, 
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #CBD5E1 !important;
        margin-bottom: 6px !important;
    }
    
    /* Dropdown wrapper background and text color styling */
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        border: 1px solid #334155 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    
    /* Selected items in multi-select */
    div[data-baseweb="tag"] {
        background-color: #8B5CF6 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    
    /* Input type values text color fix */
    input[type="text"], input[type="number"], .stNumberInput input {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Dropdown popover list container styling */
    div[data-baseweb="popover"], [role="listbox"], ul[role="listbox"] {
        background-color: #111827 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        padding: 8px 12px !important;
        transition: background-color 0.15s !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #8B5CF6 !important;
        color: #FFFFFF !important;
    }
    
    /* Collapsible Key Metrics styling */
    div[data-testid="stExpander"] {
        background-color: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Outfit', sans-serif !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        padding: 12px 18px !important;
        background-color: #0F172A !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary:hover {
        color: #8B5CF6 !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 16px !important;
        background-color: #111827 !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Tabs styling overrides */
    button[data-baseweb="tab"] {
        color: #94A3B8 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #8B5CF6 !important;
        border-bottom-width: 3px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #8B5CF6 !important;
    }
    div[data-testid="stTab"] {
        background-color: #020617 !important;
    }

    /* AgGrid Custom Alpine Dark Theme Overrides */
    .ag-theme-alpine, .ag-theme-alpine-dark {
        --ag-background-color: #0F172A !important;
        --ag-header-background-color: #111827 !important;
        --ag-header-foreground-color: #FFFFFF !important;
        --ag-foreground-color: #FFFFFF !important;
        --ag-row-hover-color: #1E293B !important;
        --ag-selected-row-background-color: rgba(139, 92, 246, 0.3) !important;
        --ag-border-color: #334155 !important;
        --ag-font-family: 'Inter', sans-serif !important;
        --ag-font-size: 16px !important;
        --ag-row-height: 50px !important;
        --ag-header-height: 50px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #334155 !important;
    }
    
    .ag-theme-alpine .ag-header, .ag-theme-alpine-dark .ag-header {
        background-color: #111827 !important;
        border-bottom: 2px solid #334155 !important;
    }
    
    .ag-theme-alpine .ag-header-cell, .ag-theme-alpine-dark .ag-header-cell {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        font-size: 18px !important; /* Header font size 18px */
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }
    
    .ag-theme-alpine .ag-header-cell-label, .ag-theme-alpine-dark .ag-header-cell-label {
        justify-content: center !important;
        letter-spacing: 0.5px;
    }
    
    .ag-theme-alpine .ag-cell, .ag-theme-alpine-dark .ag-cell {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-right: 1px solid rgba(51, 65, 85, 0.4) !important;
        color: #FFFFFF !important;
        font-size: 16px !important; /* Row font size 16px */
    }
    
    .ag-theme-alpine .ag-cell[col-id="Company"], .ag-theme-alpine-dark .ag-cell[col-id="Company"] {
        justify-content: flex-start !important;
    }
    
    .ag-theme-alpine .ag-row, .ag-theme-alpine-dark .ag-row {
        border-bottom-color: #334155 !important;
        transition: background-color 0.15s !important;
    }
    .ag-theme-alpine .ag-row-odd, .ag-theme-alpine-dark .ag-row-odd {
        background-color: #111827 !important; /* Alternate Rows #111827 */
    }
    .ag-theme-alpine .ag-row-even, .ag-theme-alpine-dark .ag-row-even {
        background-color: #0F172A !important; /* Rows #0F172A */
    }
    .ag-theme-alpine .ag-row-hover, .ag-theme-alpine-dark .ag-row-hover,
    .ag-theme-alpine .ag-row:hover, .ag-theme-alpine-dark .ag-row:hover {
        background-color: #1E293B !important; /* Hover Row #1E293B */
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #020617;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
    
    /* Status indicators */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .status-dot.online { background-color: #22C55E; box-shadow: 0 0 8px #22C55E; }
    .status-dot.offline { background-color: #EF4444; }
    .status-dot.syncing { background-color: #F59E0B; box-shadow: 0 0 8px #F59E0B; animation: blinker 1.5s linear infinite; }
    
    @keyframes blinker {
        50% { opacity: 0.3; }
    }
    </style>
    """

def get_tv_mode_css():
    """
    Returns custom CSS optimized for OBS streaming and large display TV mode.
    High contrast, hidden headers/menus, massive fonts, and pure black elements.
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Roboto+Mono:wght@500;700&family=Inter:wght@600;700&display=swap');
    
    /* Pure Black Background for OBS overlay keying and ultimate distance contrast */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Hide sidebar and headers in TV mode */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Force main content container to occupy 100% width and reduce standard padding */
    [data-testid="stAppViewBlockContainer"] {
        padding: 1.5rem 2.5rem !important;
        max-width: 100% !important;
    }
    
    /* TV Mode Header */
    .tv-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 3px solid #334155;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    
    .tv-header-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 38px;
        text-transform: uppercase;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #38BDF8 0%, #8B5CF6 50%, #EF4444 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .tv-header-time {
        font-family: 'Roboto Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    /* Giant TV Metric Cards */
    .tv-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 16px;
        margin-bottom: 25px;
    }
    
    .tv-card {
        background: #000000;
        border: 2px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: left;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.8);
    }
    
    .tv-card.accent {
        border-color: #8B5CF6;
        background: linear-gradient(135deg, #090514 0%, #000000 100%);
    }
    
    .tv-label {
        font-size: 13px;
        color: #94A3B8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    
    .tv-value {
        font-size: 36px;
        font-weight: 900;
        color: #FFFFFF;
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Giant TV Alert Banner */
    .tv-alert-banner {
        background: #7f1d1d;
        border: 3px solid #EF4444;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 25px;
        box-shadow: 0 0 30px rgba(255, 59, 48, 0.5);
        animation: flash-obs 1.2s infinite alternate;
    }
    
    @keyframes flash-obs {
        0% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); background-color: #580c0c; }
        100% { box-shadow: 0 0 35px rgba(239, 68, 68, 0.8); background-color: #7f1d1d; }
    }
    
    .tv-alert-header {
        font-size: 20px;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    
    .tv-alert-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 15px;
    }
    
    .tv-alert-val {
        font-size: 28px;
        font-weight: 900;
        color: #FFFFFF;
    }
    .tv-alert-val.sym { color: #F59E0B; }
    .tv-alert-val.qty { color: #38BDF8; }
    .tv-alert-val.val { color: #22C55E; }
    .tv-alert-val.time { font-family: 'Roboto Mono', monospace; }

    /* AgGrid TV Mode Overrides */
    .tv-aggrid-container .ag-theme-alpine, 
    .tv-aggrid-container .ag-theme-alpine-dark {
        --ag-background-color: #000000 !important;
        --ag-header-background-color: #111827 !important;
        --ag-header-foreground-color: #FFFFFF !important;
        --ag-foreground-color: #FFFFFF !important;
        --ag-border-color: #334155 !important;
        --ag-font-family: 'Outfit', sans-serif !important;
        --ag-font-size: 20px !important;
        --ag-row-height: 60px !important;
        --ag-header-height: 60px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 2px solid #334155 !important;
    }
    
    .tv-aggrid-container .ag-header,
    .tv-aggrid-container .ag-header-row {
        background-color: #111827 !important;
    }
    
    .tv-aggrid-container .ag-header-cell {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        font-size: 22px !important; /* TV Mode header size 22px */
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }
    
    .tv-aggrid-container .ag-header-cell-label {
        font-size: 22px !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        justify-content: center !important;
    }
    
    .tv-aggrid-container .ag-cell {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important; /* TV Mode rows size 20px */
        color: #FFFFFF !important;
        border-right: 1px solid rgba(51, 65, 85, 0.5) !important;
    }
    
    .tv-aggrid-container .ag-cell[col-id="Company"] {
        justify-content: flex-start !important;
    }
    
    .tv-aggrid-container .ag-row {
        border-bottom: 2px solid #334155 !important;
    }
    .tv-aggrid-container .ag-row-odd {
        background-color: #111827 !important; /* Alternate Rows #111827 */
    }
    .tv-aggrid-container .ag-row-even {
        background-color: #000000 !important; /* TV mode pure black */
    }
    .tv-aggrid-container .ag-row-hover,
    .tv-aggrid-container .ag-row:hover {
        background-color: #1E293B !important; /* Hover Row #1E293B */
    }
    
    /* Floating Exit Button */
    .tv-exit-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 10000;
        opacity: 0.3;
        transition: opacity 0.2s;
    }
    .tv-exit-container:hover {
        opacity: 1.0;
    }
    </style>
    """

def get_grid_custom_css():
    """
    Returns custom CSS dictionary to be passed to AgGrid's custom_css parameter for standard mode tables.
    """
    return {
        ".ag-theme-alpine": {
            "--ag-background-color": "#0F172A !important",
            "--ag-header-background-color": "#111827 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-row-hover-color": "#1E293B !important",
            "--ag-selected-row-background-color": "rgba(139, 92, 246, 0.3) !important",
            "--ag-border-color": "#334155 !important",
            "--ag-font-family": "'Inter', sans-serif !important",
            "--ag-font-size": "16px !important",
            "--ag-row-height": "50px !important",
            "--ag-header-height": "50px !important",
        },
        ".ag-theme-alpine-dark": {
            "--ag-background-color": "#0F172A !important",
            "--ag-header-background-color": "#111827 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-row-hover-color": "#1E293B !important",
            "--ag-selected-row-background-color": "rgba(139, 92, 246, 0.3) !important",
            "--ag-border-color": "#334155 !important",
            "--ag-font-family": "'Inter', sans-serif !important",
            "--ag-font-size": "16px !important",
            "--ag-row-height": "50px !important",
            "--ag-header-height": "50px !important",
        },
        # Overall wrapper and body backgrounds to prevent white grid canvas bleed
        ".ag-root-wrapper": {
            "background-color": "#0F172A !important",
            "border": "1px solid #334155 !important"
        },
        ".ag-root-wrapper-body": {
            "background-color": "#0F172A !important"
        },
        ".ag-root": {
            "background-color": "#0F172A !important"
        },
        ".ag-body-viewport": {
            "background-color": "#0F172A !important"
        },
        ".ag-body-horizontal-scroll-viewport": {
            "background-color": "#0F172A !important"
        },
        ".ag-body-vertical-scroll-viewport": {
            "background-color": "#0F172A !important"
        },
        ".ag-horizontal-right-spacer": {
            "background-color": "#0F172A !important",
            "border-left": "1px solid #334155 !important"
        },
        ".ag-horizontal-left-spacer": {
            "background-color": "#0F172A !important"
        },
        ".ag-stub-cell": {
            "background-color": "#0F172A !important"
        },
        ".ag-row": {
            "background-color": "#0F172A !important",
            "border-bottom-color": "#334155 !important"
        },
        ".ag-row-odd": {
            "background-color": "#111827 !important"
        },
        ".ag-row-even": {
            "background-color": "#0F172A !important"
        },
        ".ag-row-hover": {
            "background-color": "#1E293B !important"
        },
        ".ag-row:hover": {
            "background-color": "#1E293B !important"
        },
        ".ag-cell": {
            "display": "flex !important",
            "align-items": "center !important",
            "justify-content": "center !important",
            "border-right": "1px solid rgba(51, 65, 85, 0.4) !important",
            "color": "#FFFFFF !important",
            "font-size": "16px !important",
            "background-color": "transparent !important"
        },
        ".ag-cell[col-id='Company']": {
            "justify-content": "flex-start !important"
        },
        ".ag-header": {
            "background-color": "#111827 !important",
            "border-bottom": "2px solid #334155 !important"
        },
        ".ag-header-cell": {
            "background-color": "#111827 !important",
            "color": "#FFFFFF !important",
            "font-size": "18px !important",
            "font-weight": "800 !important",
            "text-transform": "uppercase !important"
        },
        ".ag-header-cell-label": {
            "justify-content": "center !important",
            "letter-spacing": "0.5px !important"
        },
        # Scrollbars customized for high-contrast dark theme inside the iframe
        "::-webkit-scrollbar": {
            "width": "8px !important",
            "height": "8px !important"
        },
        "::-webkit-scrollbar-track": {
            "background": "#020617 !important"
        },
        "::-webkit-scrollbar-thumb": {
            "background": "#334155 !important",
            "border-radius": "4px !important"
        },
        "::-webkit-scrollbar-thumb:hover": {
            "background": "#475569 !important"
        },
        "::-webkit-scrollbar-corner": {
            "background": "#020617 !important"
        }
    }

def get_grid_tv_css():
    """
    Returns custom CSS dictionary to be passed to AgGrid's custom_css parameter for TV mode.
    """
    return {
        ".ag-theme-alpine": {
            "--ag-background-color": "#000000 !important",
            "--ag-header-background-color": "#111827 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-border-color": "#334155 !important",
            "--ag-font-family": "'Outfit', sans-serif !important",
            "--ag-font-size": "20px !important",
            "--ag-row-height": "60px !important",
            "--ag-header-height": "60px !important",
        },
        ".ag-theme-alpine-dark": {
            "--ag-background-color": "#000000 !important",
            "--ag-header-background-color": "#111827 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-border-color": "#334155 !important",
            "--ag-font-family": "'Outfit', sans-serif !important",
            "--ag-font-size": "20px !important",
            "--ag-row-height": "60px !important",
            "--ag-header-height": "60px !important",
        },
        # Overall wrapper and body backgrounds to match pure black TV terminal layout
        ".ag-root-wrapper": {
            "background-color": "#000000 !important",
            "border": "2px solid #334155 !important"
        },
        ".ag-root-wrapper-body": {
            "background-color": "#000000 !important"
        },
        ".ag-root": {
            "background-color": "#000000 !important"
        },
        ".ag-body-viewport": {
            "background-color": "#000000 !important"
        },
        ".ag-body-horizontal-scroll-viewport": {
            "background-color": "#000000 !important"
        },
        ".ag-body-vertical-scroll-viewport": {
            "background-color": "#000000 !important"
        },
        ".ag-horizontal-right-spacer": {
            "background-color": "#000000 !important",
            "border-left": "1px solid #334155 !important"
        },
        ".ag-horizontal-left-spacer": {
            "background-color": "#000000 !important"
        },
        ".ag-stub-cell": {
            "background-color": "#000000 !important"
        },
        ".ag-row": {
            "background-color": "#000000 !important",
            "border-bottom-color": "#334155 !important"
        },
        ".ag-row-odd": {
            "background-color": "#111827 !important"
        },
        ".ag-row-even": {
            "background-color": "#000000 !important"
        },
        ".ag-row-hover": {
            "background-color": "#1E293B !important"
        },
        ".ag-row:hover": {
            "background-color": "#1E293B !important"
        },
        ".ag-cell": {
            "display": "flex !important",
            "align-items": "center !important",
            "justify-content": "center !important",
            "font-size": "20px !important",
            "color": "#FFFFFF !important",
            "border-right": "1px solid rgba(51, 65, 85, 0.5) !important",
            "background-color": "transparent !important"
        },
        ".ag-cell[col-id='Company']": {
            "justify-content": "flex-start !important"
        },
        ".ag-header": {
            "background-color": "#111827 !important"
        },
        ".ag-header-row": {
            "background-color": "#111827 !important"
        },
        ".ag-header-cell": {
            "background-color": "#111827 !important",
            "color": "#FFFFFF !important",
            "font-size": "22px !important",
            "font-weight": "800 !important",
            "text-transform": "uppercase !important"
        },
        ".ag-header-cell-label": {
            "font-size": "22px !important",
            "font-weight": "900 !important",
            "text-transform": "uppercase !important",
            "justify-content": "center !important"
        },
        # Scrollbars customized for high-contrast dark TV theme inside the iframe
        "::-webkit-scrollbar": {
            "width": "8px !important",
            "height": "8px !important"
        },
        "::-webkit-scrollbar-track": {
            "background": "#000000 !important"
        },
        "::-webkit-scrollbar-thumb": {
            "background": "#334155 !important",
            "border-radius": "4px !important"
        },
        "::-webkit-scrollbar-thumb:hover": {
            "background": "#475569 !important"
        },
        "::-webkit-scrollbar-corner": {
            "background": "#000000 !important"
        }
    }

