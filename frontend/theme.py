"""Sistema visual del frontend Streamlit."""

from __future__ import annotations

import streamlit as st


THEME_CSS = """
<style>
:root {
    --navy-950: #071525;
    --navy-900: #0b1f35;
    --navy-800: #12314f;
    --ink-900: #102235;
    --ink-700: #40566d;
    --ink-500: #718398;
    --line: #dbe5ee;
    --surface: rgba(255, 255, 255, .92);
    --teal: #0d9488;
    --teal-dark: #0f766e;
    --cyan: #22d3ee;
    --green: #15966a;
    --amber: #d89a22;
    --red: #d9535f;
    --shadow: 0 16px 42px rgba(24, 48, 75, .09);
}

html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", system-ui, -apple-system, sans-serif;
}

[data-testid="stAppViewContainer"] {
    color: var(--ink-900);
    background:
        radial-gradient(circle at 8% 5%, rgba(34, 211, 238, .10), transparent 26rem),
        radial-gradient(circle at 96% 12%, rgba(13, 148, 136, .08), transparent 28rem),
        #f4f7fa;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; }

.block-container {
    max-width: 1240px;
    padding-top: 2.15rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    color: var(--ink-900);
    letter-spacing: -.035em;
}
h1 { font-size: clamp(2rem, 4vw, 3.25rem) !important; line-height: 1.05 !important; }
h2 { font-size: 1.75rem !important; margin-top: .25rem !important; }
h3 { font-size: 1.12rem !important; }
p { color: var(--ink-700); }

[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 10% 0%, rgba(34, 211, 238, .18), transparent 19rem),
        linear-gradient(165deg, var(--navy-950), var(--navy-900));
    border-right: 1px solid rgba(255, 255, 255, .08);
}
[data-testid="stSidebar"] * { color: #eaf4fb; }
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(255, 255, 255, .08);
    border: 1px solid rgba(255, 255, 255, .12);
}
[data-testid="stSidebar"] .stButton > button {
    color: #eaf4fb !important;
    border-color: rgba(255,255,255,.18) !important;
    background: rgba(255,255,255,.07) !important;
}
[data-testid="stSidebar"] .stButton > button p { color: #eaf4fb !important; }

.brand-lockup { padding: .5rem .1rem 1.25rem; }
.brand-mark {
    display: inline-grid;
    place-items: center;
    width: 2.55rem;
    height: 2.55rem;
    margin-bottom: .8rem;
    border-radius: .85rem;
    color: #062331;
    font-size: 1.25rem;
    font-weight: 900;
    background: linear-gradient(135deg, var(--cyan), #5eead4);
    box-shadow: 0 10px 24px rgba(34, 211, 238, .22);
}
.brand-name { color: #fff; font-size: 1.15rem; font-weight: 760; letter-spacing: -.02em; }
.brand-copy { color: #94aabd; font-size: .78rem; line-height: 1.5; margin-top: .28rem; }

.eyebrow {
    color: var(--teal-dark);
    font-size: .72rem;
    font-weight: 800;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: -.35rem;
}
.context-strip {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: .55rem;
    margin: .1rem 0 1.25rem;
}
.context-pill {
    display: inline-flex;
    align-items: center;
    gap: .38rem;
    padding: .42rem .7rem;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: rgba(255,255,255,.72);
    color: var(--ink-700);
    font-size: .76rem;
    font-weight: 650;
}
.context-dot { width: .46rem; height: .46rem; border-radius: 50%; background: var(--green); }

[data-testid="stForm"], [data-testid="stExpander"] {
    border: 1px solid rgba(207, 220, 231, .95) !important;
    border-radius: 1.1rem !important;
    background: var(--surface) !important;
    box-shadow: 0 10px 30px rgba(24, 48, 75, .055);
}
[data-testid="stForm"] { padding: 1.25rem 1.3rem 1.3rem; }

[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div {
    border-color: #cedae5 !important;
    border-radius: .72rem !important;
    background: #f8fafc !important;
}
[data-baseweb="input"] > div:focus-within,
[data-baseweb="textarea"] > div:focus-within {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px rgba(13, 148, 136, .12) !important;
}

.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {
    min-height: 2.75rem;
    border-radius: .72rem !important;
    border: 1px solid #cbd8e3 !important;
    font-weight: 720 !important;
    transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stLinkButton"] a:hover {
    transform: translateY(-1px);
    border-color: var(--teal) !important;
    box-shadow: 0 8px 20px rgba(13, 148, 136, .12);
}
.stButton > button:disabled, .stDownloadButton > button:disabled {
    opacity: .46 !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"], button[kind="primaryFormSubmit"] {
    color: white !important;
    border: 0 !important;
    background: linear-gradient(135deg, var(--teal-dark), var(--teal)) !important;
    box-shadow: 0 10px 22px rgba(13, 148, 136, .20);
}
.stButton > button[kind="primary"] p,
button[kind="primaryFormSubmit"] p { color: white !important; }

[data-testid="stFileUploaderDropzone"] {
    padding: 1.5rem !important;
    border: 1.5px dashed #9bb6c8 !important;
    border-radius: 1rem !important;
    background: linear-gradient(135deg, rgba(236, 253, 245, .7), rgba(240, 249, 255, .8)) !important;
}

[data-testid="stTabs"] [role="tablist"] {
    gap: .45rem;
    padding: .38rem;
    border: 1px solid var(--line);
    border-radius: .9rem;
    background: rgba(255,255,255,.72);
}
[data-testid="stTabs"] button[role="tab"] {
    min-height: 2.6rem;
    padding: .55rem .9rem;
    border-radius: .65rem;
    color: var(--ink-500);
    font-weight: 680;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--teal-dark);
    background: white;
    box-shadow: 0 4px 14px rgba(24, 48, 75, .09);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none; }

[data-testid="stMetric"] {
    min-height: 7rem;
    padding: 1rem 1.05rem;
    border: 1px solid var(--line);
    border-radius: 1rem;
    background: linear-gradient(145deg, #fff, #f8fbfd);
    box-shadow: 0 9px 24px rgba(24, 48, 75, .055);
}
[data-testid="stMetricLabel"] { color: var(--ink-500); font-weight: 680; }
[data-testid="stMetricValue"] { color: var(--ink-900); letter-spacing: -.04em; }

[data-testid="stAlert"] {
    border: 0 !important;
    border-left: 4px solid currentColor !important;
    border-radius: .75rem !important;
}
[data-testid="stChatMessage"] {
    border: 1px solid var(--line);
    border-radius: 1rem;
    background: rgba(255,255,255,.82);
}
[data-testid="stDataFrame"] {
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: .9rem;
    box-shadow: 0 8px 24px rgba(24, 48, 75, .045);
}
hr { border-color: var(--line) !important; margin: 2rem 0 !important; }

.auth-shell { padding: 4vh 0 2rem; }
.auth-kicker {
    display: inline-flex;
    padding: .42rem .72rem;
    margin-bottom: 1rem;
    color: var(--teal-dark);
    background: #ddf7f2;
    border: 1px solid #b9ebe1;
    border-radius: 999px;
    font-size: .74rem;
    font-weight: 800;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.auth-title {
    max-width: 720px;
    margin: 0 0 1rem;
    color: var(--ink-900);
    font-size: clamp(2.55rem, 5vw, 4.65rem);
    font-weight: 820;
    line-height: .98;
    letter-spacing: -.06em;
}
.auth-title span { color: var(--teal); }
.auth-lead { max-width: 600px; color: var(--ink-700); font-size: 1.03rem; line-height: 1.7; }
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; margin-top: 1.5rem; }
.feature-card {
    padding: .9rem;
    border: 1px solid var(--line);
    border-radius: .9rem;
    background: rgba(255,255,255,.72);
}
.feature-card b { display: block; color: var(--ink-900); font-size: .86rem; }
.feature-card span { color: var(--ink-500); font-size: .72rem; }
.login-panel-title { margin: .2rem 0 .2rem; color: var(--ink-900); font-size: 1.35rem; font-weight: 780; }
.login-panel-copy { margin-bottom: 1rem; color: var(--ink-500); font-size: .82rem; }
.legal-note { color: var(--ink-500); font-size: .72rem; line-height: 1.5; }

@media (max-width: 850px) {
    .block-container { padding-top: 1.25rem; }
    .auth-shell { padding-top: 0; }
    .feature-grid { grid-template-columns: 1fr; }
    [data-testid="column"] { min-width: 100% !important; }
    [data-testid="stTabs"] [role="tablist"] { overflow-x: auto; }
}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def section_eyebrow(label: str) -> None:
    st.markdown(f'<div class="eyebrow">{label}</div>', unsafe_allow_html=True)


def context_strip(items: list[str]) -> None:
    pills = "".join(
        f'<span class="context-pill"><span class="context-dot"></span>{item}</span>'
        for item in items
    )
    st.markdown(f'<div class="context-strip">{pills}</div>', unsafe_allow_html=True)


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-mark">R</div>
            <div class="brand-name">RiskLens Finance</div>
            <div class="brand-copy">Análisis financiero explicable<br>con evidencia y control humano.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
