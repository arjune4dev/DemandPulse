
import streamlit as st


THEMES = {
    "Dark": {
        "page": "#0B1020",
        "sidebar": "#0E1729",
        "surface": "#121D31",
        "surface2": "#19263C",
        "border": "#26354D",
        "text": "#F1F5F9",
        "muted": "#8FA1B8",
        "accent": "#638BFF",
        "accent2": "#8B9FFF",
        "success": "#36C99A",
        "warning": "#F4B860",
        "danger": "#F27683",
        "grid": "#26354D",
    },
    "Light": {
        "page": "#F4F6FA",
        "sidebar": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface2": "#F8FAFD",
        "border": "#E5EAF2",
        "text": "#172238",
        "muted": "#718096",
        "accent": "#4169E1",
        "accent2": "#718BFF",
        "success": "#159D75",
        "warning": "#D99428",
        "danger": "#DC5968",
        "grid": "#E8EDF4",
    },
}


def setup_ui(page_title="DemandPulse"):
    if "dp_theme" not in st.session_state:
        st.session_state.dp_theme = "Dark"

    st.set_page_config(
        page_title=page_title,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    theme = st.session_state.dp_theme
    colors = THEMES[theme]

    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {colors["page"]};
            --sidebar: {colors["sidebar"]};
            --surface: {colors["surface"]};
            --surface2: {colors["surface2"]};
            --border: {colors["border"]};
            --text: {colors["text"]};
            --muted: {colors["muted"]};
            --accent: {colors["accent"]};
        }}

        .stApp {{
            background: var(--bg);
            color: var(--text);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stSidebar"] {{
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background: var(--sidebar);
        }}

        .block-container {{
            max-width: 1560px;
            padding: 2rem 3.25rem 3.5rem 3.25rem;
        }}

        h1, h2, h3, h4 {{
            color: var(--text) !important;
            letter-spacing: -0.7px;
        }}

        p, label {{
            color: var(--muted);
        }}

        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, var(--surface), var(--surface2));
            border: 1px solid var(--border);
            border-top: 3px solid var(--accent);
            border-radius: 16px;
            padding: 17px 19px 15px;
            min-height: 118px;
            box-shadow: 0 10px 28px rgba(0,0,0,.12);
            transition: transform .18s ease, box-shadow .18s ease;
        }}

        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 32px rgba(0,0,0,.18);
        }}

        [data-testid="stMetricLabel"] p {{
            color: var(--muted) !important;
            font-size: 12px;
            font-weight: 650;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--text) !important;
            font-size: 25px;
            font-weight: 780;
            letter-spacing: -.8px;
        }}

        [data-testid="stMetricDelta"] {{ font-size: 11px; }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}

        .dp-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0 35px 0;
        }}

        .dp-logo {{
            width: 42px;
            height: 42px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg,#4169E1,#8B9FFF);
            color: white;
            font-size: 22px;
            font-weight: 900;
        }}

        .dp-brand-name {{
            font-size: 19px;
            font-weight: 800;
            color: var(--text);
            letter-spacing: -0.6px;
        }}

        .dp-brand-sub {{
            color: var(--muted);
            font-size: 9px;
            letter-spacing: 2px;
            font-weight: 700;
        }}

        .dp-label {{
            color: var(--muted);
            font-size: 10px;
            letter-spacing: 1.8px;
            font-weight: 800;
            margin: 20px 0 12px 0;
        }}

        .dp-header {{
            margin-bottom: 26px;
        }}

        .dp-eyebrow {{
            font-size: 10px;
            color: var(--accent);
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 9px;
        }}

        .dp-title {{
            color: var(--text);
            font-size: 32px;
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -1.3px;
        }}

        .dp-subtitle {{
            color: var(--muted);
            font-size: 13px;
            margin-top: 9px;
        }}

        .dp-hero {{
            position: relative;
            overflow: hidden;
            padding: 34px 38px;
            border-radius: 22px;
            background: radial-gradient(ellipse at 83% 25%, rgba(89,139,255,.42), transparent 35%), linear-gradient(115deg,#101D35,#183B77 62%,#244FAE);
            border: 1px solid rgba(255,255,255,.12);
            box-shadow: 0 18px 48px rgba(20,52,108,.22);
            margin-bottom: 30px;
        }}

        .dp-hero-layout {{ display: flex; align-items: center; justify-content: space-between; gap: 36px; }}
        .dp-hero-content {{ max-width: 720px; }}
        .dp-live-dot {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #56E0B2; box-shadow: 0 0 12px rgba(86,224,178,.8); margin-right: 7px; vertical-align: 1px; }}

        .dp-hero-tag {{
            color: #BBD0FF;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
        }}

        .dp-hero-title {{
            color: #FFFFFF;
            font-size: clamp(28px, 3vw, 38px);
            font-weight: 800;
            letter-spacing: -1px;
            margin-top: 13px;
        }}

        .dp-hero-copy {{
            color: #D8E5FF;
            font-size: 13px;
            line-height: 1.7;
            max-width: 600px;
            margin-top: 9px;
        }}

        .dp-hero-aside {{ min-width: 228px; padding: 19px 21px; border-radius: 16px; border: 1px solid rgba(255,255,255,.18); background: rgba(8,21,47,.28); backdrop-filter: blur(12px); }}
        .dp-hero-aside-label {{ color: #BBD0FF; font-size: 9px; letter-spacing: 1.5px; font-weight: 800; }}
        .dp-hero-aside-value {{ color: #fff; font-size: 35px; font-weight: 800; letter-spacing: -1px; margin-top: 9px; }}
        .dp-hero-aside-value span {{ font-size: 14px; font-weight: 600; letter-spacing: 0; color: #D8E5FF; }}
        .dp-hero-aside-rule {{ display: flex; align-items: end; gap: 5px; height: 24px; margin-top: 11px; }}
        .dp-hero-aside-rule i {{ flex: 1; height: 35%; border-radius: 4px; background: #78A1FF; opacity: .75; }}
        .dp-hero-aside-rule i:nth-child(2) {{ height: 55%; }} .dp-hero-aside-rule i:nth-child(3) {{ height: 45%; }} .dp-hero-aside-rule i:nth-child(4) {{ height: 75%; }} .dp-hero-aside-rule i:nth-child(5) {{ height: 60%; }} .dp-hero-aside-rule i:nth-child(6) {{ height: 90%; }} .dp-hero-aside-rule i:nth-child(7) {{ height: 100%; background: #54DBB4; }}
        .dp-hero-aside-foot {{ color: #D8E5FF; font-size: 10px; margin-top: 12px; }}

        .dp-section {{
            color: var(--text);
            font-size: 17px;
            font-weight: 750;
            letter-spacing: -.4px;
            margin: 30px 0 6px 0;
            padding-left: 12px;
            border-left: 3px solid var(--accent);
        }}

        .dp-section-sub {{
            color: var(--muted);
            font-size: 11px;
            margin-bottom: 17px;
        }}

        .dp-kpi {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 19px;
            min-height: 126px;
        }}

        .dp-kpi-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .dp-kpi-label {{
            color: var(--muted);
            font-size: 11px;
            font-weight: 650;
        }}

        .dp-kpi-icon {{
            width: 31px;
            height: 31px;
            border-radius: 9px;
            background: var(--surface2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
        }}

        .dp-kpi-value {{
            color: var(--text);
            font-size: 25px;
            font-weight: 800;
            letter-spacing: -.8px;
            margin-top: 13px;
        }}

        .dp-kpi-note {{
            color: var(--muted);
            font-size: 10px;
            margin-top: 5px;
        }}

        .dp-panel {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 20px;
        }}

        .dp-card {{
            position: relative;
            display: flex;
            flex-direction: column;
            min-height: 228px;
            padding: 23px;
            overflow: hidden;
            border-radius: 18px;
            border: 1px solid var(--border);
            background: radial-gradient(circle at 100% 0%, rgba(99,139,255,.12), transparent 42%), linear-gradient(145deg,var(--surface),var(--surface2));
            box-shadow: 0 12px 28px rgba(0,0,0,.10);
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }}

        .dp-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent);
            box-shadow: 0 18px 36px rgba(0,0,0,.18);
        }}

        .dp-card-top {{ display: flex; align-items: center; gap: 11px; }}
        .dp-card-icon {{
            display: flex; align-items: center; justify-content: center;
            width: 40px; height: 40px; border-radius: 13px;
            color: white; font-size: 20px; font-weight: 800;
            background: linear-gradient(135deg,#4169E1,#8B9FFF);
            box-shadow: 0 7px 18px rgba(65,105,225,.28);
        }}
        .dp-card-label {{ color: var(--accent); font-size: 9px; letter-spacing: 1.7px; font-weight: 850; }}
        .dp-card-value {{ color: var(--text); font-size: 20px; line-height: 1.2; font-weight: 780; letter-spacing: -.5px; margin-top: 24px; }}
        .dp-card-foot {{ color: var(--muted); font-size: 12px; line-height: 1.65; margin-top: 7px; max-width: 290px; }}
        .dp-card-meta {{ display: flex; align-items: center; justify-content: space-between; color: var(--muted); font-size: 9px; letter-spacing: 1px; font-weight: 800; margin-top: auto; padding-top: 22px; }}
        .dp-card-meta span {{ color: var(--accent); font-size: 16px; }}

        .dp-next-step {{ display: flex; align-items: center; gap: 15px; margin-top: 20px; padding: 17px 20px; border: 1px solid rgba(99,139,255,.30); border-radius: 15px; background: linear-gradient(100deg,rgba(99,139,255,.13),rgba(99,139,255,.04)); }}
        .dp-next-step-icon {{ display: flex; align-items: center; justify-content: center; flex: 0 0 38px; height: 38px; color: white; border-radius: 12px; background: linear-gradient(135deg,#4169E1,#8B9FFF); font-size: 18px; }}
        .dp-next-step strong {{ color: var(--text); font-size: 12px; }}
        .dp-next-step div span {{ color: var(--muted); font-size: 11px; }}
        .dp-next-step-hint {{ margin-left: auto; color: var(--accent); font-size: 9px; letter-spacing: 1px; font-weight: 850; white-space: nowrap; }}

        [data-testid="stSidebarNav"] {{ padding-top: 12px; }}
        [data-testid="stSidebarNav"] a {{ border-radius: 10px; margin: 3px 0; }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{ background: rgba(99,139,255,.16); color: var(--text); }}
        [data-testid="stSidebar"] [data-testid="stCaption"] p {{ opacity: 1; color: var(--muted) !important; }}

        [data-testid="stPlotlyChart"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 8px;
            overflow: hidden;
        }}

        [data-testid="stDataFrame"] {{
            background: var(--surface);
            border-color: var(--border);
            border-radius: 14px;
        }}

        [data-testid="stAlert"] {{ border-radius: 12px; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{ border-radius: 9px 9px 0 0; }}

        @media (max-width: 900px) {{
            .block-container {{ padding: 1.5rem 1.1rem 2rem 1.1rem; }}
            .dp-hero {{ padding: 26px 23px; }}
            .dp-title {{ font-size: 27px; }}
            .dp-hero-aside {{ display: none; }}
            .dp-next-step-hint {{ display: none; }}
        }}

        .dp-status {{
            display: inline-block;
            padding: 6px 10px;
            border-radius: 20px;
            background: {colors["surface2"]};
            color: {colors["accent"]};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .7px;
        }}

        .dp-footer {{
            border-top: 1px solid var(--border);
            padding-top: 18px;
            margin-top: 40px;
            color: var(--muted);
            font-size: 10px;
            letter-spacing: 1px;
        }}

        .stButton > button {{
            border-radius: 9px;
            font-weight: 700;
            min-height: 42px;
        }}

        .stButton > button[kind="primary"] {{
            background: var(--accent);
            color: white;
            border: none;
        }}

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {{
            background: var(--surface2);
            border-color: var(--border);
            border-radius: 9px;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown(
            """
            <div class="dp-brand">
                <div class="dp-logo">D</div>
                <div>
                    <div class="dp-brand-name">DemandPulse</div>
                    <div class="dp-brand-sub">RETAIL INTELLIGENCE</div>
                </div>
            </div>
            <div class="dp-label">WORKSPACE</div>
            """,
            unsafe_allow_html=True,
        )

        st.selectbox(
            "Appearance",
            ["Dark", "Light"],
            key="dp_theme",
        )

        st.markdown(
            """
            <div class="dp-label">PLATFORM</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='dp-label'>CAPABILITIES</div>",
            unsafe_allow_html=True,
        )
        st.caption("◉  Seven-day demand forecasts")
        st.caption("◈  Inventory scenario planning")
        st.caption("⌁  Model monitoring & explainability")

    return colors


def page_header(title, subtitle, eyebrow="DEMANDPULSE / ANALYTICS"):
    st.markdown(
        f"""
        <div class="dp-header">
            <div class="dp-eyebrow">{eyebrow}</div>
            <div class="dp-title">{title}</div>
            <div class="dp-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    description = (
        f'<div class="dp-section-sub">{subtitle}</div>'
        if subtitle else ""
    )

    st.markdown(
        f"""
        <div class="dp-section">{title}</div>
        {description}
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, icon="◈", note=""):
    st.markdown(
        f"""
        <div class="dp-kpi">
            <div class="dp-kpi-top">
                <div class="dp-kpi-label">{label}</div>
                <div class="dp-kpi-icon">{icon}</div>
            </div>
            <div class="dp-kpi-value">{value}</div>
            <div class="dp-kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_theme(colors):
    return {
        "paper_bgcolor": colors["surface"],
        "plot_bgcolor": colors["surface"],
        "font": {
            "color": colors["text"],
            "family": "Inter, sans-serif",
        },
        "xaxis": {
            "gridcolor": colors["grid"],
            "linecolor": colors["border"],
        },
        "yaxis": {
            "gridcolor": colors["grid"],
            "linecolor": colors["border"],
        },
        "margin": {"l": 15, "r": 15, "t": 35, "b": 15},
        "hovermode": "x unified",
    }
