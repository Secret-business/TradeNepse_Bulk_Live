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
        background-color: #030712 !important;
        color: #94A3B8 !important;
        font-size: 15px !important;
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
        margin-top: 30px;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1E293B;
    }
    .section-header-icon {
        font-size: 24px;
    }
    .section-header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }
    
    /* Primary / Accent Buttons */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #6D28D9 !important;
        border-color: #6D28D9 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 10px rgba(109, 40, 217, 0.2) !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #7C3AED !important;
        border-color: #7C3AED !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 15px rgba(124, 58, 237, 0.4) !important;
    }
    
    /* Outline / Secondary / Export Buttons */
    div[data-testid="stButton"] button[kind="secondary"], 
    div[data-testid="stDownloadButton"] button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover, 
    div[data-testid="stDownloadButton"] button:hover {
        border-color: #6D28D9 !important;
        color: #FFFFFF !important;
        background-color: #1E293B !important;
        box-shadow: 0 0 8px rgba(109, 40, 217, 0.15) !important;
    }
    
    /* Premium 4-Card Dashboard KPI Grid */
    .dashboard-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }

    .kpi-card {
        background: linear-gradient(135deg, #0F172A 0%, #0B0F19 100%) !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 120px;
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #6D28D9, #3B82F6);
        opacity: 0.8;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: #6D28D9 !important;
        box-shadow: 0 6px 20px rgba(109, 40, 217, 0.25);
    }

    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }

    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.8px;
    }

    .kpi-icon {
        font-size: 18px;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: rgba(109, 40, 217, 0.1);
        color: #A78BFA;
        border: 1px solid rgba(109, 40, 217, 0.2);
    }

    .kpi-value {
        font-family: 'Outfit', sans-serif;
        font-size: 26px !important;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.5px;
        margin: 12px 0 4px 0;
    }

    .kpi-sub {
        font-size: 11px;
        color: #64748B;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
        
    /* Live Bulk Alert Banner */
    .live-bulk-alert-container {
        background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%) !important;
        border: 1px solid #6D28D9 !important;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(109, 40, 217, 0.2);
        animation: pulse-alert-border 2s infinite alternate;
    }
    
    @keyframes pulse-alert-border {
        0% {
            border-color: #4C1D95;
            box-shadow: 0 0 8px rgba(109, 40, 217, 0.2);
        }
        100% {
            border-color: #8B5CF6;
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
        }
    }
    
    /* Filter Bar Box */
    .filter-panel {
        background-color: #0B0F19 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .filter-title {
        font-family: 'Outfit', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: #A78BFA;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* Form Inputs and Select Boxes Overrides */
    div[data-testid="stSelectbox"] label, 
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        margin-bottom: 4px !important;
    }
    
    /* Dropdown wrapper background and text color styling */
    div[data-baseweb="select"] > div {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    
    /* Selected items in multi-select */
    div[data-baseweb="tag"] {
        background-color: #6D28D9 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    
    /* Input type values text color fix */
    input[type="text"], input[type="number"], .stNumberInput input {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }
    
    /* Dropdown popover list container styling */
    div[data-baseweb="popover"], [role="listbox"], ul[role="listbox"] {
        background-color: #0B0F19 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        background-color: #0B0F19 !important;
        color: #FFFFFF !important;
        padding: 8px 12px !important;
        transition: background-color 0.15s !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #6D28D9 !important;
        color: #FFFFFF !important;
    }
    
    /* Collapsible Metric styling */
    div[data-testid="stExpander"] {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Outfit', sans-serif !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        padding: 12px 18px !important;
        background-color: #0F172A !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary:hover {
        color: #A78BFA !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 16px !important;
        background-color: #0B0F19 !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Tabs styling overrides */
    button[data-baseweb="tab"] {
        color: #64748B !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #6D28D9 !important;
        border-bottom-width: 3px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #A78BFA !important;
    }
    div[data-testid="stTab"] {
        background-color: #030712 !important;
    }

    /* AgGrid Custom Alpine Dark Theme Overrides */
    .ag-theme-alpine, .ag-theme-alpine-dark {
        --ag-background-color: #0B0F19 !important;
        --ag-header-background-color: #0F172A !important;
        --ag-header-foreground-color: #FFFFFF !important;
        --ag-foreground-color: #FFFFFF !important;
        --ag-row-hover-color: #1E293B !important;
        --ag-selected-row-background-color: rgba(109, 40, 217, 0.3) !important;
        --ag-border-color: #1E293B !important;
        --ag-font-family: 'Inter', sans-serif !important;
        --ag-font-size: 14px !important;
        --ag-row-height: 44px !important;
        --ag-header-height: 46px !important;
        font-weight: 500 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #1E293B !important;
    }
    
    .ag-theme-alpine .ag-header, .ag-theme-alpine-dark .ag-header {
        background-color: #0F172A !important;
        border-bottom: 2px solid #1E293B !important;
    }
    
    .ag-theme-alpine .ag-header-cell, .ag-theme-alpine-dark .ag-header-cell {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-size: 13px !important;
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
        border-right: 1px solid rgba(30, 41, 59, 0.4) !important;
        color: #FFFFFF !important;
        font-size: 14px !important;
    }
    
    .ag-theme-alpine .ag-cell[col-id="Company"], .ag-theme-alpine-dark .ag-cell[col-id="Company"] {
        justify-content: flex-start !important;
    }
    
    .ag-theme-alpine .ag-row, .ag-theme-alpine-dark .ag-row {
        border-bottom-color: #1E293B !important;
        transition: background-color 0.15s !important;
    }
    .ag-theme-alpine .ag-row-odd, .ag-theme-alpine-dark .ag-row-odd {
        background-color: #0B0F19 !important;
    }
    .ag-theme-alpine .ag-row-even, .ag-theme-alpine-dark .ag-row-even {
        background-color: #0F172A !important;
    }
    .ag-theme-alpine .ag-row-hover, .ag-theme-alpine-dark .ag-row-hover,
    .ag-theme-alpine .ag-row:hover, .ag-theme-alpine-dark .ag-row:hover {
        background-color: #1E293B !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #030712;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
    
    /* Status indicators */
    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .status-dot.online { background-color: #10B981; box-shadow: 0 0 8px #10B981; }
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
        border-bottom: 3px solid #1E293B;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    
    .tv-header-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 36px;
        text-transform: uppercase;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 50%, #F87171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .tv-header-time {
        font-family: 'Roboto Mono', monospace;
        font-size: 24px;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    /* Giant TV Metric Cards */
    .tv-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 25px;
    }
    
    .tv-card {
        background: #0B0F19;
        border: 2px solid #1E293B;
        border-radius: 12px;
        padding: 16px;
        text-align: left;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.8);
    }
    
    .tv-card.accent {
        border-color: #6D28D9;
        background: linear-gradient(135deg, #120A2A 0%, #000000 100%);
    }
    
    .tv-label {
        font-size: 12px;
        color: #94A3B8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    
    .tv-value {
        font-size: 32px;
        font-weight: 900;
        color: #FFFFFF;
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.5px;
    }
    
    /* Giant TV Alert Banner */
    .tv-alert-banner {
        background: #4C1D95;
        border: 2px solid #8B5CF6;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 25px;
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
        animation: flash-obs 1.5s infinite alternate;
    }
    
    @keyframes flash-obs {
        0% { box-shadow: 0 0 10px rgba(139, 92, 246, 0.3); background-color: #2E1065; }
        100% { box-shadow: 0 0 30px rgba(139, 92, 246, 0.6); background-color: #4C1D95; }
    }
    
    .tv-alert-header {
        font-size: 18px;
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
        font-size: 24px;
        font-weight: 900;
        color: #FFFFFF;
    }
    .tv-alert-val.sym { color: #A78BFA; }
    .tv-alert-val.qty { color: #60A5FA; }
    .tv-alert-val.val { color: #34D399; }
    .tv-alert-val.time { font-family: 'Roboto Mono', monospace; }

    /* AgGrid TV Mode Overrides */
    .tv-aggrid-container .ag-theme-alpine, 
    .tv-aggrid-container .ag-theme-alpine-dark {
        --ag-background-color: #000000 !important;
        --ag-header-background-color: #0B0F19 !important;
        --ag-header-foreground-color: #FFFFFF !important;
        --ag-foreground-color: #FFFFFF !important;
        --ag-border-color: #1E293B !important;
        --ag-font-family: 'Outfit', sans-serif !important;
        --ag-font-size: 18px !important;
        --ag-row-height: 54px !important;
        --ag-header-height: 54px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 2px solid #1E293B !important;
    }
    
    .tv-aggrid-container .ag-header,
    .tv-aggrid-container .ag-header-row {
        background-color: #0B0F19 !important;
    }
    
    .tv-aggrid-container .ag-header-cell {
        background-color: #0B0F19 !important;
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }
    
    .tv-aggrid-container .ag-header-cell-label {
        font-size: 18px !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        justify-content: center !important;
    }
    
    .tv-aggrid-container .ag-cell {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 18px !important;
        color: #FFFFFF !important;
        border-right: 1px solid rgba(30, 41, 59, 0.5) !important;
    }
    
    .tv-aggrid-container .ag-cell[col-id="Company"] {
        justify-content: flex-start !important;
    }
    
    .tv-aggrid-container .ag-row {
        border-bottom: 2px solid #1E293B !important;
    }
    .tv-aggrid-container .ag-row-odd {
        background-color: #0B0F19 !important;
    }
    .tv-aggrid-container .ag-row-even {
        background-color: #000000 !important;
    }
    .tv-aggrid-container .ag-row-hover,
    .tv-aggrid-container .ag-row:hover {
        background-color: #1E293B !important;
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
            "--ag-background-color": "#0B0F19 !important",
            "--ag-header-background-color": "#0F172A !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-row-hover-color": "#1E293B !important",
            "--ag-selected-row-background-color": "rgba(109, 40, 217, 0.3) !important",
            "--ag-border-color": "#1E293B !important",
            "--ag-font-family": "'Inter', sans-serif !important",
            "--ag-font-size": "14px !important",
            "--ag-row-height": "44px !important",
            "--ag-header-height": "46px !important",
        },
        ".ag-theme-alpine-dark": {
            "--ag-background-color": "#0B0F19 !important",
            "--ag-header-background-color": "#0F172A !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-row-hover-color": "#1E293B !important",
            "--ag-selected-row-background-color": "rgba(109, 40, 217, 0.3) !important",
            "--ag-border-color": "#1E293B !important",
            "--ag-font-family": "'Inter', sans-serif !important",
            "--ag-font-size": "14px !important",
            "--ag-row-height": "44px !important",
            "--ag-header-height": "46px !important",
        },
        ".ag-root-wrapper": {
            "background-color": "#0B0F19 !important",
            "border": "1px solid #1E293B !important"
        },
        ".ag-root-wrapper-body": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-root": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-body-viewport": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-body-horizontal-scroll-viewport": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-body-vertical-scroll-viewport": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-horizontal-right-spacer": {
            "background-color": "#0B0F19 !important",
            "border-left": "1px solid #1E293B !important"
        },
        ".ag-horizontal-left-spacer": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-stub-cell": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-row": {
            "background-color": "#0B0F19 !important",
            "border-bottom-color": "#1E293B !important"
        },
        ".ag-row-odd": {
            "background-color": "#0B0F19 !important"
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
            "border-right": "1px solid rgba(30, 41, 59, 0.4) !important",
            "color": "#FFFFFF !important",
            "font-size": "14px !important",
            "background-color": "transparent !important"
        },
        ".ag-cell[col-id='Company']": {
            "justify-content": "flex-start !important"
        },
        ".ag-header": {
            "background-color": "#0F172A !important",
            "border-bottom": "2px solid #1E293B !important"
        },
        ".ag-header-cell": {
            "background-color": "#0F172A !important",
            "color": "#FFFFFF !important",
            "font-size": "13px !important",
            "font-weight": "800 !important",
            "text-transform": "uppercase !important"
        },
        ".ag-header-cell-label": {
            "justify-content": "center !important",
            "letter-spacing": "0.5px !important"
        },
        "::-webkit-scrollbar": {
            "width": "8px !important",
            "height": "8px !important"
        },
        "::-webkit-scrollbar-track": {
            "background": "#030712 !important"
        },
        "::-webkit-scrollbar-thumb": {
            "background": "#1E293B !important",
            "border-radius": "4px !important"
        },
        "::-webkit-scrollbar-thumb:hover": {
            "background": "#334155 !important"
        },
        "::-webkit-scrollbar-corner": {
            "background": "#030712 !important"
        }
    }

def get_grid_tv_css():
    """
    Returns custom CSS dictionary to be passed to AgGrid's custom_css parameter for TV mode.
    """
    return {
        ".ag-theme-alpine": {
            "--ag-background-color": "#000000 !important",
            "--ag-header-background-color": "#0B0F19 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-border-color": "#1E293B !important",
            "--ag-font-family": "'Outfit', sans-serif !important",
            "--ag-font-size": "18px !important",
            "--ag-row-height": "54px !important",
            "--ag-header-height": "54px !important",
        },
        ".ag-theme-alpine-dark": {
            "--ag-background-color": "#000000 !important",
            "--ag-header-background-color": "#0B0F19 !important",
            "--ag-header-foreground-color": "#FFFFFF !important",
            "--ag-foreground-color": "#FFFFFF !important",
            "--ag-border-color": "#1E293B !important",
            "--ag-font-family": "'Outfit', sans-serif !important",
            "--ag-font-size": "18px !important",
            "--ag-row-height": "54px !important",
            "--ag-header-height": "54px !important",
        },
        ".ag-root-wrapper": {
            "background-color": "#000000 !important",
            "border": "2px solid #1E293B !important"
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
            "border-left": "1px solid #1E293B !important"
        },
        ".ag-horizontal-left-spacer": {
            "background-color": "#000000 !important"
        },
        ".ag-stub-cell": {
            "background-color": "#000000 !important"
        },
        ".ag-row": {
            "background-color": "#000000 !important",
            "border-bottom-color": "#1E293B !important"
        },
        ".ag-row-odd": {
            "background-color": "#0B0F19 !important"
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
            "font-size": "18px !important",
            "color": "#FFFFFF !important",
            "border-right": "1px solid rgba(30, 41, 59, 0.5) !important",
            "background-color": "transparent !important"
        },
        ".ag-cell[col-id='Company']": {
            "justify-content": "flex-start !important"
        },
        ".ag-header": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-header-row": {
            "background-color": "#0B0F19 !important"
        },
        ".ag-header-cell": {
            "background-color": "#0B0F19 !important",
            "color": "#FFFFFF !important",
            "font-size": "18px !important",
            "font-weight": "800 !important",
            "text-transform": "uppercase !important"
        },
        ".ag-header-cell-label": {
            "font-size": "18px !important",
            "font-weight": "900 !important",
            "text-transform": "uppercase !important",
            "justify-content": "center !important"
        },
        "::-webkit-scrollbar": {
            "width": "8px !important",
            "height": "8px !important"
        },
        "::-webkit-scrollbar-track": {
            "background": "#000000 !important"
        },
        "::-webkit-scrollbar-thumb": {
            "background": "#1E293B !important",
            "border-radius": "4px !important"
        },
        "::-webkit-scrollbar-thumb:hover": {
            "background": "#334155 !important"
        },
        "::-webkit-scrollbar-corner": {
            "background": "#000000 !important"
        }
    }
