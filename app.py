import os
from html import escape
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE CONFIG & STYLE
# ---------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Relay AI Strategy Dashboard",
    initial_sidebar_state="expanded"
)

COLOR_WARN = "#C55A44"       # red / risk
COLOR_SAFE = "#598259"       # green / safe
COLOR_NEUTRAL = "#344622"    # dark green
COLOR_BG = "#FDFCF0"
COLOR_CARD = "#FFFFFF"
COLOR_GRID = "rgba(52,70,34,0.12)"
COLOR_AMBER = "#D5A04C"

st.markdown(f"""
<style>
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3, h4, p, span, div, label, li {{ color: {COLOR_NEUTRAL} !important; }}
    [data-testid="stSidebar"] {{ background-color: #262730 !important; }}
    [data-testid="stSidebar"] * {{ color: #FDFCF0 !important; }}

    .badge-vsm {{ border: 1px solid #A46B52; color: #A46B52 !important; padding: 4px 9px; border-radius: 4px; font-size: 0.78rem; font-weight: bold; margin-right: 6px; text-transform: uppercase;}}
    .badge-thrive {{ border: 1px solid #598259; color: #598259 !important; padding: 4px 9px; border-radius: 4px; font-size: 0.78rem; font-weight: bold; margin-right: 6px; text-transform: uppercase;}}

    .explanation-box {{ background-color: #FFFFFF; padding: 24px; border-radius: 8px; border-left: 5px solid #E75124; margin-top: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
    .explanation-box h4 {{ margin-top: 0; color: #E75124 !important; margin-bottom: 12px; font-size: 1.2rem;}}
    .safe-box {{ background-color:#F6FBF4; border:1px solid #C9DEC3; border-left:5px solid {COLOR_SAFE}; border-radius:8px; padding:22px; margin-top:18px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }}
    .risk-board {{ background: linear-gradient(135deg, #FFF7F3 0%, #FFFFFF 72%); border: 1px solid #E7B4A6; border-left: 8px solid {COLOR_WARN}; border-radius: 14px; padding: 22px 24px; margin-top: 22px; box-shadow: 0 8px 22px rgba(197,90,68,0.15); }}
    .risk-board h3 {{ margin-top: 0; margin-bottom: 8px; color: {COLOR_WARN} !important; font-size: 1.45rem; }}
    .risk-summary {{ display:flex; gap:14px; flex-wrap:wrap; margin: 14px 0 18px 0; }}
    .risk-pill {{ background:#FFFFFF; border:1px solid #E7B4A6; border-radius:12px; padding:12px 16px; min-width:150px; box-shadow:0 4px 10px rgba(0,0,0,0.04); }}
    .risk-pill .label {{ font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:#7C574B !important; font-weight:700; }}
    .risk-pill .value {{ font-size:1.55rem; font-weight:800; color:{COLOR_WARN} !important; line-height:1.1; }}
    .attention-table {{ width:100%; border-collapse:separate; border-spacing:0 8px; font-size:0.95rem; }}
    .attention-table th {{ text-align:left; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.07em; color:#7C574B !important; padding:0 12px 4px 12px; }}
    .attention-table td {{ background:#FFFFFF; padding:12px; border-top:1px solid #F0D1C8; border-bottom:1px solid #F0D1C8; font-size:0.95rem; }}
    .attention-table td:first-child {{ border-left:1px solid #F0D1C8; border-radius:10px 0 0 10px; font-weight:800; }}
    .attention-table td:last-child {{ border-right:1px solid #F0D1C8; border-radius:0 10px 10px 0; }}
    .priority-badge {{ display:inline-block; background:{COLOR_WARN}; color:white !important; font-weight:800; border-radius:999px; padding:5px 10px; font-size:0.75rem; }}
    .watch-badge {{ display:inline-block; background:#D5A04C; color:white !important; font-weight:800; border-radius:999px; padding:5px 10px; font-size:0.75rem; }}
    .bar-track {{ width:100%; height:12px; background:#F3E5DF; border-radius:999px; overflow:hidden; }}
    .bar-fill {{ height:12px; background:{COLOR_WARN}; border-radius:999px; }}
    .metric-card {{ background-color:#FFFFFF; border:1px solid #D5D5D5; border-radius:10px; padding:18px; min-height: 120px; box-shadow: 0 3px 8px rgba(0,0,0,0.04); }}
    .verbatim-grid {{ display:grid; grid-template-columns: 1fr; gap:10px; margin-top:10px; }}
    .verbatim-card {{ background:#FFFFFF; border-radius:10px; padding:12px 14px; border:1px solid #D8D8D8; box-shadow:0 3px 9px rgba(0,0,0,0.04); min-height:78px; }}
    .verbatim-card.good {{ border-left:5px solid #598259; }}
    .verbatim-card.bad {{ border-left:5px solid #C55A44; }}
    .verbatim-card .meta {{ font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.04em; opacity:0.8; margin-bottom:6px; }}
    .verbatim-card .quote {{ font-size:0.95rem; line-height:1.38; }}
    .section-label {{ font-size:0.85rem; font-weight:900; text-transform:uppercase; letter-spacing:0.08em; margin-top:14px; margin-bottom:6px; }}
    hr {{ border-color: rgba(174, 234, 128, 0.5); margin-top: 10px; margin-bottom: 20px;}}
    div.stButton > button {{ background-color: #344622; color: white !important; border: none; border-radius: 6px; padding: 10px; font-weight: bold;}}
    div.stButton > button:hover {{ background-color: #598259; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------
def find_file(*names):
    for name in names:
        if os.path.exists(name):
            return name
    return None


def read_csv_required(label, *names, required_cols=None):
    path = find_file(*names)
    if path is None:
        st.error(f"Missing required CSV for {label}: {', '.join(names)}")
        return None
    try:
        df = pd.read_csv(path, sep=";", encoding="utf-8-sig", on_bad_lines="skip")
    except Exception as exc:
        st.error(f"Could not read {path}: {exc}")
        return None
    df.columns = df.columns.astype(str).str.strip()
    if required_cols:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(f"{path} is missing columns: {missing}. Found: {df.columns.tolist()}")
            return None
    return df


def to_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.strip()
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )


def bool_series(series):
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "sim"])


def fig_layout(fig, height=430):
    """Common chart styling: larger labels, cleaner executive layout, no distracting grid mesh."""
    fig.update_layout(
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font=dict(color=COLOR_NEUTRAL, size=15),
        title=dict(font=dict(size=20, color=COLOR_NEUTRAL), x=0.0, y=0.97, xanchor="left", yanchor="top"),
        height=height,
        margin=dict(l=70, r=105, t=105, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13)
        ),
        hoverlabel=dict(bgcolor="white", font_size=14, font_color=COLOR_NEUTRAL),
    )
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="rgba(52,70,34,0.45)",
        linewidth=1,
        zeroline=False,
        tickfont=dict(size=14),
        title_font=dict(size=16),
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=False,
        showline=True,
        linecolor="rgba(52,70,34,0.45)",
        linewidth=1,
        zeroline=False,
        tickfont=dict(size=14),
        title_font=dict(size=16),
        automargin=True,
    )
    return fig


def show_source_table(df, title="View exact source values used in this chart", fmt=None):
    with st.expander(title):
        if fmt:
            st.dataframe(df.style.format(fmt))
        else:
            st.dataframe(df)


def render_stock_attention_board(attention_df):
    """Render a polished HTML risk board without letting Markdown treat HTML as a code block."""
    if attention_df.empty:
        st.markdown(
            "<div class='safe-box'><h4>✅ No SKU families above forecast</h4>"
            "<p>Actual demand did not exceed forecast for any SKU family in the selected period.</p></div>",
            unsafe_allow_html=True,
        )
        return

    df = attention_df.sort_values("missing_units", ascending=False).copy()
    total_gap = float(df["missing_units"].sum())
    top_gap = float(df.iloc[0]["missing_units"])
    top_family = escape(str(df.iloc[0]["SKU_family"]))
    max_gap = float(df["missing_units"].max())

    rows = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        family = escape(str(row["SKU_family"]))
        demand = float(row["demand_units"])
        forecast = float(row["forecast_units"])
        gap = float(row["missing_units"])
        share = gap / total_gap if total_gap else 0
        width = max(6, min(100, gap / max_gap * 100)) if max_gap else 0
        badge = "CRITICAL" if idx <= 3 else "WATCH"
        badge_class = "priority-badge" if idx <= 3 else "watch-badge"
        rows.append(
            "<tr>"
            f"<td><b>{idx}. {family}</b></td>"
            f"<td>{demand:,.0f}</td>"
            f"<td>{forecast:,.0f}</td>"
            f"<td><b style='color:{COLOR_WARN} !important;'>+{gap:,.0f}</b></td>"
            f"<td>{share:.1%}</td>"
            f"<td><div class='bar-track'><div class='bar-fill' style='width:{width:.1f}%;'></div></div></td>"
            f"<td><span class='{badge_class}'>{badge}</span></td>"
            "</tr>"
        )

    html = (
        "<div class='risk-board'>"
        "<h3>🚨 SKU families needing stock attention</h3>"
        "<p>Actual demand exceeded forecast in these families. The board ranks stockout pressure by real unit gap from the CSV.</p>"
        "<div class='risk-summary'>"
        f"<div class='risk-pill'><div class='label'>Families flagged</div><div class='value'>{len(df)}</div></div>"
        f"<div class='risk-pill'><div class='label'>Total unit gap</div><div class='value'>+{total_gap:,.0f}</div></div>"
        f"<div class='risk-pill'><div class='label'>Highest gap</div><div class='value'>+{top_gap:,.0f}</div></div>"
        f"<div class='risk-pill'><div class='label'>Top risk family</div><div class='value' style='font-size:1.05rem;'>{top_family}</div></div>"
        "</div>"
        "<table class='attention-table'>"
        "<thead><tr><th>SKU family</th><th>Demand</th><th>Forecast</th><th>Unit gap</th><th>Share of gap</th><th>Pressure</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def clean_review_text(value, max_chars=185):
    text = str(value).strip().replace("\n", " ")
    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "..."
    return text


def render_verbatim_cards(reviews_df):
    """Render 5 positive and 5 negative review cards with clean HTML, not raw code blocks."""
    if reviews_df is None or reviews_df.empty:
        st.info("No review verbatims available in the current data.")
        return

    good = (
        reviews_df[reviews_df["rating"] >= 4]
        .sort_values("date", ascending=False)
        .head(5)
        .copy()
    )
    bad = (
        reviews_df[reviews_df["rating"] <= 2]
        .sort_values("date", ascending=False)
        .head(5)
        .copy()
    )

    def card_html(row, kind):
        emoji = "✅" if kind == "good" else "⚠️"
        label = "Positive" if kind == "good" else "Negative"
        date_value = row.get("date")
        date_label = date_value.strftime("%Y-%m-%d") if pd.notna(date_value) else "No date"
        rating_value = row.get("rating", "N/A")
        try:
            rating_label = f"{float(rating_value):.0f}"
        except Exception:
            rating_label = str(rating_value)
        text = escape(clean_review_text(row.get("text", "")))
        return (
            f"<div class='verbatim-card {kind}'>"
            f"<div class='meta'>{emoji} {label} · {escape(date_label)} · Rating {escape(rating_label)}</div>"
            f"<div class='quote'>❝ {text} ❞</div>"
            "</div>"
        )

    st.markdown("<div class='section-label'>✅ Positive community signals</div>", unsafe_allow_html=True)
    good_html = "<div class='verbatim-grid'>" + "".join(card_html(row, "good") for _, row in good.iterrows()) + "</div>"
    st.markdown(good_html, unsafe_allow_html=True)

    st.markdown("<div class='section-label'>⚠️ Negative community signals</div>", unsafe_allow_html=True)
    bad_html = "<div class='verbatim-grid'>" + "".join(card_html(row, "bad") for _, row in bad.iterrows()) + "</div>"
    st.markdown(bad_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 3. NAVIGATION
# ---------------------------------------------------------
if "aba_atual" not in st.session_state:
    st.session_state.aba_atual = "🏠 Overview"


def mudar_aba(nova_aba):
    st.session_state.aba_atual = nova_aba


st.sidebar.markdown("## 🏃 Relay AI Dashboard")
st.sidebar.markdown("---")
st.sidebar.markdown("**THE ROOT QUESTION**")
st.sidebar.info("RELAY GETS HEALTHIER WHEN...\n\n... the people who already chose us come back, feel heard, and are reached in time — not when more strangers discover us.")
st.sidebar.markdown("---")

aba = st.sidebar.radio(
    "Navigation",
    ["🏠 Overview", "📊 KPI 1: LTV:CAC", "🗣️ KPI 2: Retention & Trust", "⚡ KPI 3: SKU Anomaly"],
    key="aba_atual"
)

debug_mode = st.sidebar.checkbox("Show data audit", value=False)


def render_kpi_header(title, vsm, thrive, what, decision, vanity):
    col_back, col_title = st.columns([1.5, 8.5])
    with col_back:
        st.button("⬅️ Back to Overview", on_click=mudar_aba, args=("🏠 Overview",), key=f"back_{title}")
    with col_title:
        st.markdown(f"<h1 style='margin-top: -15px;'>{title}</h1>", unsafe_allow_html=True)

    st.markdown(f"<div><span class='badge-vsm'>{vsm}</span> <span class='badge-thrive'>{thrive}</span></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background-color: #FFFFFF; padding: 22px; border-radius: 8px; border: 1px solid #D5D5D5; margin-top: 15px; margin-bottom: 25px;'>
        <p style='font-size: 1.25rem; margin-bottom: 12px; line-height:1.45;'><b>What it counts:</b> {what}</p>
        <p style='font-size: 1.25rem; margin-bottom: 12px; line-height:1.45;'><b>The decision it drives:</b> {decision}</p>
        <p style='font-size: 1.25rem; margin-bottom: 0; line-height:1.45;'><b>The Vanity Test:</b> {vanity}</p>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# 4. LOAD DATA
# ---------------------------------------------------------
dados = {}
audit = {}

# 4.1 Returns processing cost
avg_return_cost = 14.31
df_returns_cost = read_csv_required(
    "returns processing",
    "returns_processing.csv",
    "returns_processing(1).csv",
    required_cols=["month", "cost_per_return_$"]
)
if df_returns_cost is not None:
    df_returns_cost["month"] = df_returns_cost["month"].astype(str)
    df_returns_cost["cost_per_return_$"] = to_number(df_returns_cost["cost_per_return_$"])
    df_returns_2025 = df_returns_cost[df_returns_cost["month"].str.startswith("2025", na=False)].copy()
    source_cost = df_returns_2025 if not df_returns_2025.empty else df_returns_cost
    avg_return_cost = float(source_cost["cost_per_return_$"].dropna().mean())
    dados["avg_return_cost"] = avg_return_cost
    audit["returns_processing"] = df_returns_cost

# 4.2 Transactions
base_cac = {
    "community_referral": 15,
    "organic": 10,
    "email": 10,
    "paid_search": 40,
    "paid_social": 65
}

df_t = read_csv_required(
    "transactions",
    "transactions_orders.csv",
    "transactions_orders(1).csv",
    required_cols=["order_id", "date", "acquisition_channel", "SKU_family", "order_value", "returned", "return_reason"]
)
if df_t is not None:
    df_t["date"] = pd.to_datetime(df_t["date"], errors="coerce")
    df_t["order_value"] = to_number(df_t["order_value"])
    df_t["returned_bool"] = bool_series(df_t["returned"])
    df_t["acquisition_channel"] = df_t["acquisition_channel"].astype(str).str.strip()

    df_t_2025 = df_t[df_t["date"].dt.year == 2025].copy()
    df_t_period = df_t_2025 if not df_t_2025.empty else df_t.copy()

    rev_by_channel = (
        df_t_period.groupby("acquisition_channel", as_index=False)
        .agg(
            total_rev=("order_value", "sum"),
            orders=("order_id", "count"),
            returns=("returned_bool", "sum")
        )
    )
    rev_by_channel["aov"] = rev_by_channel["total_rev"] / rev_by_channel["orders"]
    rev_by_channel["return_rate"] = rev_by_channel["returns"] / rev_by_channel["orders"]
    rev_by_channel["base_cac"] = rev_by_channel["acquisition_channel"].map(base_cac)
    rev_by_channel["effective_cac"] = rev_by_channel["base_cac"] + (rev_by_channel["return_rate"] * avg_return_cost)
    rev_by_channel["ltv_cac_ratio"] = rev_by_channel["aov"] / rev_by_channel["effective_cac"]
    rev_by_channel = rev_by_channel.dropna(subset=["ltv_cac_ratio"]).copy()
    rev_by_channel = rev_by_channel.sort_values("ltv_cac_ratio", ascending=True)
    dados["kpi1_data"] = rev_by_channel

    sizing_df = df_t_period[
        (df_t_period["returned_bool"] == True)
        & (df_t_period["return_reason"].fillna("").astype(str).str.lower().str.strip() == "sizing")
    ]
    dados["total_returns"] = int(df_t_period["returned_bool"].sum())
    dados["sizing_returns"] = int(len(sizing_df))
    audit["transactions_orders"] = df_t_period

# 4.3 Reviews
_df_r = read_csv_required(
    "reviews",
    "reviews_text.csv",
    "reviews_text(1).csv",
    required_cols=["source", "date", "rating", "text"]
)
if _df_r is not None:
    df_r = _df_r.copy()
    df_r["date"] = pd.to_datetime(df_r["date"], errors="coerce")
    df_r["rating"] = pd.to_numeric(df_r["rating"], errors="coerce")
    df_reviews_only = df_r[df_r["rating"].notna()].copy()
    df_reviews_only["month_dt"] = df_reviews_only["date"].dt.to_period("M").dt.to_timestamp()
    df_reviews_only["month"] = df_reviews_only["month_dt"].dt.strftime("%b %Y")
    df_reviews_only["is_erosion"] = (df_reviews_only["rating"] <= 2).astype(int)

    erosion_trend = (
        df_reviews_only.groupby(["month_dt", "month"], as_index=False)
        .agg(
            total_reviews=("rating", "count"),
            negative_signals=("is_erosion", "sum")
        )
        .sort_values("month_dt")
    )
    erosion_trend["erosion_rate"] = (erosion_trend["negative_signals"] / erosion_trend["total_reviews"]) * 100
    erosion_trend = erosion_trend[erosion_trend["month_dt"].dt.year == 2025].copy()
    dados["kpi2_trend"] = erosion_trend.tail(8)
    dados["reviews"] = df_reviews_only.copy()
    audit["reviews_text"] = df_reviews_only

# 4.4 Inventory forecast
_df_i = read_csv_required(
    "inventory forecast",
    "inventory_forecast.csv",
    "inventory_forecast(1).csv",
    required_cols=["month", "SKU_family", "demand_units", "forecast_units"]
)
if _df_i is not None:
    df_i = _df_i.copy()
    df_i["month_dt"] = pd.to_datetime(df_i["month"], errors="coerce")
    df_i["demand_units"] = to_number(df_i["demand_units"])
    df_i["forecast_units"] = to_number(df_i["forecast_units"])
    df_i_2025 = df_i[df_i["month_dt"].dt.year == 2025].copy()
    df_i_period = df_i_2025 if not df_i_2025.empty else df_i.copy()

    sku_all = (
        df_i_period.groupby("SKU_family", as_index=False)
        .agg(demand_units=("demand_units", "sum"), forecast_units=("forecast_units", "sum"))
    )
    sku_all["missing_units"] = sku_all["demand_units"] - sku_all["forecast_units"]
    sku_all["status"] = sku_all["missing_units"].apply(lambda x: "Demand above forecast" if x > 0 else "Forecast sufficient")
    sku_all = sku_all.sort_values("missing_units", ascending=True)
    dados["kpi3_all_sku"] = sku_all
    dados["kpi3_attention"] = sku_all[sku_all["missing_units"] > 0].sort_values("missing_units", ascending=False)
    dados["checkpoint_var"] = int(sku_all.loc[sku_all["SKU_family"].eq("Checkpoint Leggings"), "missing_units"].sum())
    audit["inventory_forecast"] = df_i_period

# 4.5 Size band return rate
_df_size = read_csv_required(
    "return rate by size band",
    "RETURN_RATE_BY_SIZE_BAND_YEAR2025.csv",
    "RETURN_RATE_BY_SIZE_BAND_YEAR2025(1).csv",
    required_cols=["size_band", "share_of_units", "return_rate_pct"]
)
if _df_size is not None:
    df_size = _df_size.copy()
    df_size["return_rate_pct"] = to_number(df_size["return_rate_pct"])
    df_size["share_of_units"] = to_number(df_size["share_of_units"])
    df_size = df_size.dropna(subset=["size_band", "return_rate_pct", "share_of_units"]).copy()
    df_size["size_band"] = df_size["size_band"].astype(str).str.strip()
    df_size["share_of_units_pct"] = df_size["share_of_units"] * 100
    size_order = ["XS", "S", "M", "L", "XL", "XXL"]
    df_size["size_order"] = df_size["size_band"].apply(lambda x: size_order.index(x) if x in size_order else 99)
    df_size = df_size.sort_values("size_order")
    dados["kpi3_size"] = df_size
    audit["return_rate_by_size_band"] = df_size

# Global cards
comm_ltv_cac, paid_ltv_cac = "N/A", "N/A"
if "kpi1_data" in dados and not dados["kpi1_data"].empty:
    df_kpi1 = dados["kpi1_data"]
    try:
        comm_ltv_cac = f"{df_kpi1[df_kpi1['acquisition_channel'] == 'community_referral']['ltv_cac_ratio'].values[0]:.1f}x"
        paid_ltv_cac = f"{df_kpi1[df_kpi1['acquisition_channel'] == 'paid_social']['ltv_cac_ratio'].values[0]:.1f}x"
    except Exception:
        pass

erosion_rate_dec = "N/A"
if "kpi2_trend" in dados and not dados["kpi2_trend"].empty:
    erosion_rate_dec = f"{dados['kpi2_trend'].iloc[-1]['erosion_rate']:.1f}%"

checkpoint_var = f"{dados.get('checkpoint_var', 0):,.0f}"
sizing_share = f"{(dados.get('sizing_returns', 0) / max(dados.get('total_returns', 1), 1) * 100):.1f}%"

if debug_mode:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data audit")
    for name, df in audit.items():
        st.sidebar.write(f"{name}: {df.shape[0]:,} rows × {df.shape[1]} cols")
        with st.sidebar.expander(name):
            st.write(df.head())


# ---------------------------------------------------------
# 5. OVERVIEW
# ---------------------------------------------------------
if aba == "🏠 Overview":
    st.markdown("<div style='display:flex; justify-content:space-between; align-items:end;'><h2>RELAY · AI Strategy Dashboard</h2><p style='color:#666;'>Live • FY2025 • v5 refined</p></div><hr style='margin-top:0;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 3rem;'>Three KPIs, <i>one instrument.</i></h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem;'>This dashboard tracks the three KPIs defined in the W6 tree. Each one lives with a named owner, watches a specific VSM subsystem, aligns with a THRIVE pillar, and reads from the Relay data workbooks.</p><br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background-color:#FDFCF0; padding:15px 25px; border-radius:10px; border:1px solid #D5D5D5; display:flex; gap:30px; align-items:center;'>
        <div><span style='background-color:#344622; color:white !important; border-radius:50%; padding:5px 8px; font-weight:bold; font-size:12px;'>HC</span> <b>Helen Cho</b> · CFO · reads KPI 1</div>
        <div><span style='background-color:#5A7B9C; color:white !important; border-radius:50%; padding:5px 6px; font-weight:bold; font-size:12px;'>SW</span> <b>Sam Whitaker</b> · Data & Ops · reads KPI 3</div>
        <div><span style='background-color:#A46B52; color:white !important; border-radius:50%; padding:5px 8px; font-weight:bold; font-size:12px;'>PS</span> <b>Priya Sharma</b> · Community · reads KPI 2</div>
    </div><br>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style='background-color:#FDFCF0; border: 2px solid #344622; border-radius:10px; padding:20px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom: 5px; height: 100%;'>
            <div><p style='color:#A46B52; font-style:italic; margin-bottom:5px; font-weight:bold;'>KPI i.</p><h3 style='margin-top:0; margin-bottom: 20px;'>Effective LTV:CAC</h3></div>
            <div>
                <div style='display:flex; justify-content:space-between; align-items:end; margin-bottom: 10px;'><h1 style='color:#598259; margin:0; font-size:2.5rem; line-height: 1;'>{comm_ltv_cac}</h1><p style='margin:0; font-size:11px; color:#666; font-weight:bold;'>COMMUNITY</p></div>
                <div style='display:flex; justify-content:space-between; align-items:end;'><h1 style='color:#C55A44; margin:0; font-size:2.5rem; line-height: 1;'>{paid_ltv_cac}</h1><p style='margin:0; font-size:11px; color:#666; font-weight:bold;'>PAID SOCIAL</p></div>
            </div>
            <hr><div><span class='badge-vsm'>S3 · OPTIMIZING</span> <span class='badge-thrive'>THRIVE E</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open KPI 1 Detail ➔", on_click=mudar_aba, args=("📊 KPI 1: LTV:CAC",), key="btn_kpi1")
    with c2:
        st.markdown(f"""
        <div style='background-color:#FDFCF0; border: 1px solid #C0D6E4; border-radius:10px; padding:20px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom: 5px; height: 100%;'>
            <div><p style='color:#A46B52; font-style:italic; margin-bottom:5px; font-weight:bold;'>KPI ii.</p><h3 style='margin-top:0; margin-bottom: 20px;'>Pacer Retention & Trust</h3></div>
            <div style='display:flex; justify-content:space-between; align-items:end;'><h1 style='color:#C55A44; margin:0; font-size:2.5rem; line-height: 1;'>{erosion_rate_dec}</h1><p style='margin:0; font-size:11px; color:#666; font-weight:bold;'>DEC EROSION RATE</p></div>
            <hr><div><span class='badge-vsm'>S4 · SENSING</span> <span class='badge-thrive'>THRIVE V</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open KPI 2 Detail ➔", on_click=mudar_aba, args=("🗣️ KPI 2: Retention & Trust",), key="btn_kpi2")
    with c3:
        st.markdown(f"""
        <div style='background-color:#FDFCF0; border: 1px solid #E2D1C3; border-radius:10px; padding:20px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom: 5px; height: 100%;'>
            <div><p style='color:#A46B52; font-style:italic; margin-bottom:5px; font-weight:bold;'>KPI iii.</p><h3 style='margin-top:0; margin-bottom: 20px;'>SKU Anomaly Response</h3></div>
            <div>
                <div style='display:flex; justify-content:space-between; align-items:end; margin-bottom: 10px;'><h1 style='color:#C55A44; margin:0; font-size:2.5rem; line-height: 1;'>{checkpoint_var}</h1><p style='margin:0; font-size:11px; color:#666; font-weight:bold;'>CHECKPOINT GAP</p></div>
                <div style='display:flex; justify-content:space-between; align-items:end;'><h1 style='color:#D5A04C; margin:0; font-size:2.5rem; line-height: 1;'>{sizing_share}</h1><p style='margin:0; font-size:11px; color:#666; font-weight:bold;'>SIZING RETURN SHARE</p></div>
            </div>
            <hr><div><span class='badge-vsm'>S2 · COORDINATING</span> <span class='badge-thrive'>THRIVE E</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Open KPI 3 Detail ➔", on_click=mudar_aba, args=("⚡ KPI 3: SKU Anomaly",), key="btn_kpi3")


# ---------------------------------------------------------
# 6. KPI 1
# ---------------------------------------------------------
elif aba == "📊 KPI 1: LTV:CAC":
    render_kpi_header(
        title="Effective LTV:CAC by Channel",
        vsm="VSM: System 3 (Optimizing)",
        thrive="THRIVE: Sustains (E-Test)",
        what="LTV:CAC ratio split by channel, computed with Effective CAC — acquisition cost plus the financial impact of returns.",
        decision="When paid Effective CAC crosses threshold, Finance re-prices channel spend and protects the community budget. <i>(Owner: Helen Cho, CFO)</i>",
        vanity="Game it by shrinking the paid cohort or under-loading returns. <b>Guard-rail:</b> Pair with absolute cohort size and gross margin after returns."
    )

    if "kpi1_data" not in dados or dados["kpi1_data"].empty:
        st.error("KPI 1 data was not loaded.")
    else:
        df = dados["kpi1_data"].copy()
        channels = df["acquisition_channel"].astype(str).tolist()
        ratios = df["ltv_cac_ratio"].astype(float).tolist()
        colors = [COLOR_SAFE if v >= 3 else COLOR_WARN for v in ratios]
        text_labels = [f"{v:.2f}x" for v in ratios]

        col_chart1, col_chart2 = st.columns([1.2, 1])
        with col_chart1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=ratios,
                y=channels,
                orientation="h",
                marker_color=colors,
                text=text_labels,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="Channel: %{y}<br>Actual LTV:CAC: %{x:.2f}x<extra></extra>",
                name="LTV:CAC"
            ))
            fig.add_vline(x=3.0, line_dash="dash", line_color=COLOR_WARN, annotation_text="Healthy target: 3.0x", annotation_position="top right")
            fig.update_layout(title="Effective Ratio by Channel", xaxis_title="Calculated LTV:CAC ratio", yaxis_title="Source channel")
            fig.update_traces(textfont=dict(size=14))
            fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, max(ratios) * 1.28])
            fig.update_yaxes(showgrid=False)
            fig = fig_layout(fig, height=440)
            st.plotly_chart(fig, use_container_width=True)

            source_kpi1 = df[["acquisition_channel", "orders", "returns", "return_rate", "aov", "effective_cac", "ltv_cac_ratio"]].rename(columns={
                "acquisition_channel": "Channel",
                "orders": "Orders",
                "returns": "Returns",
                "return_rate": "Return rate",
                "aov": "AOV",
                "effective_cac": "Effective CAC",
                "ltv_cac_ratio": "LTV:CAC"
            })
            show_source_table(source_kpi1, fmt={"Return rate": "{:.1%}", "AOV": "${:,.2f}", "Effective CAC": "${:,.2f}", "LTV:CAC": "{:.2f}x"})

            top_channel = df.sort_values("ltv_cac_ratio", ascending=False).iloc[0]
            weak_channel = df.sort_values("ltv_cac_ratio", ascending=True).iloc[0]
            st.markdown(f"""
            <div class='explanation-box'>
                <h4>📊 Chart explanation</h4>
                <p>This chart is calculated from <code>transactions_orders.csv</code>. It groups orders by acquisition channel, computes average order value and return rate, then adjusts CAC using the dynamic return-processing cost from <code>returns_processing.csv</code>.</p>
                <p><b>Best channel:</b> {top_channel['acquisition_channel']} at <b>{top_channel['ltv_cac_ratio']:.2f}x</b>. <b>Weakest channel:</b> {weak_channel['acquisition_channel']} at <b>{weak_channel['ltv_cac_ratio']:.2f}x</b>.</p>
                <p><b>Reading:</b> Values below the 3.0x target indicate channels where return burden and acquisition economics weaken profitable growth.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_chart2:
            try:
                val_paid = float(df[df["acquisition_channel"].eq("paid_social")]["ltv_cac_ratio"].values[0])
            except Exception:
                val_paid = 0.0
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=val_paid,
                number={"suffix": "x", "valueformat": ".2f"},
                title={"text": ""},
                domain={"x": [0, 1], "y": [0, 0.86]},
                gauge={
                    "axis": {"range": [0, max(8, max(ratios) * 1.15)]},
                    "bar": {"color": COLOR_WARN if val_paid < 3 else COLOR_SAFE},
                    "steps": [
                        {"range": [0, 1.5], "color": "rgba(197, 90, 68, 0.22)"},
                        {"range": [1.5, 3], "color": "rgba(213, 160, 76, 0.18)"},
                        {"range": [3, max(8, max(ratios) * 1.15)], "color": "rgba(89, 130, 89, 0.26)"}
                    ],
                    "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.75, "value": 3.0}
                }
            ))
            fig_gauge.update_layout(
                plot_bgcolor=COLOR_BG,
                paper_bgcolor=COLOR_BG,
                font=dict(color=COLOR_NEUTRAL, size=16),
                title=dict(
                    text="Paid Social LTV:CAC Ratio",
                    x=0.5,
                    y=0.98,
                    xanchor="center",
                    yanchor="top",
                    font=dict(size=20, color=COLOR_NEUTRAL)
                ),
                height=380,
                margin=dict(l=40, r=40, t=105, b=35)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"""
            <div class='explanation-box'>
                <h4>🧮 Calculation logic</h4>
                <p><b>Effective CAC</b> = Base CAC + Return Rate × Average Return Cost.</p>
                <p>The average return cost is read from <code>returns_processing.csv</code>: <b>${avg_return_cost:.2f}</b>.</p>
                <p><b>Executive conclusion:</b> Paid Social produces volume but carries a weaker LTV:CAC profile after the return burden is included. Community Referral remains the more resilient growth channel.</p>
            </div>
            """, unsafe_allow_html=True)


# ---------------------------------------------------------
# 7. KPI 2
# ---------------------------------------------------------
elif aba == "🗣️ KPI 2: Retention & Trust":
    render_kpi_header(
        title="Pacer Retention & Trust Sentiment",
        vsm="VSM: System 4 (Sensing) & 5 (Identity)",
        thrive="THRIVE: Sustains (E-Test)",
        what="Trust erosion rate calculated as the percentage of 1 and 2-star reviews among rated customer reviews.",
        decision="When trust sentiment deteriorates, Community reviews AI touchpoints and pauses autonomous content to protect the brand. <i>(Owner: Priya Sharma)</i>",
        vanity="Game it by retuning the sentiment classifier. <b>Guard-rail:</b> Pair with hard Pacer churn metrics and weekly human audits."
    )

    if "kpi2_trend" not in dados or dados["kpi2_trend"].empty:
        st.error("KPI 2 data was not loaded.")
    else:
        df = dados["kpi2_trend"].copy().sort_values("month_dt")
        months = df["month"].tolist()
        rates = df["erosion_rate"].astype(float).tolist()
        labels = [f"{v:.1f}%" for v in rates]

        col1, col2 = st.columns([1.45, 1])
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months,
                y=rates,
                mode="lines+markers+text",
                text=labels,
                textposition="top center",
                line=dict(width=4, color=COLOR_WARN),
                marker=dict(size=10, color=COLOR_WARN),
                hovertemplate="Month: %{x}<br>Erosion rate: %{y:.1f}%<extra></extra>",
                name="Trust erosion rate"
            ))
            fig.update_layout(title="Trust Erosion Rate (% of 1 and 2-Star Reviews)", xaxis_title="Timeline (2025)", yaxis_title="Erosion rate (%)")
            fig.update_traces(textfont=dict(size=13))
            fig.update_yaxes(range=[0, 100], ticksuffix="%", showgrid=False)
            fig.update_xaxes(showgrid=False)
            fig = fig_layout(fig, height=460)
            st.plotly_chart(fig, use_container_width=True)

            source_kpi2 = df[["month", "total_reviews", "negative_signals", "erosion_rate"]].rename(columns={
                "month": "Month",
                "total_reviews": "Total reviews",
                "negative_signals": "1–2 star reviews",
                "erosion_rate": "Erosion rate"
            })
            show_source_table(source_kpi2, fmt={"Erosion rate": "{:.1f}%"})

            latest = df.iloc[-1]
            st.markdown(f"""
            <div class='explanation-box'>
                <h4>📈 Chart explanation</h4>
                <p>The CSV does not contain an explicit erosion-rate column. The dashboard calculates it as <b>1–2 star reviews ÷ total rated reviews × 100</b>.</p>
                <p><b>Latest reading:</b> {latest['month']} reached <b>{latest['erosion_rate']:.1f}%</b>, based on <b>{int(latest['negative_signals'])}</b> negative reviews out of <b>{int(latest['total_reviews'])}</b> rated reviews.</p>
                <p>The Y-axis is fixed at <b>0–100%</b>, so the line represents a true percentage trend rather than an indexed scale.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='explanation-box' style='border-left-color: #344622; margin-top: 0;'>
                <h4 style='color: #344622 !important;'>🧠 CSV Deep-Dive & Diagnostics</h4>
                <p>The right-side panel intentionally focuses on interpretation instead of repeating the same information as a second chart.</p>
                <ul>
                    <li><b>Metric source:</b> <code>rating</code> and <code>text</code> fields from <code>reviews_text.csv</code>.</li>
                    <li><b>Calculation:</b> Trust erosion = 1–2 star reviews ÷ total rated reviews × 100.</li>
                    <li><b>Break point:</b> September marks the visible acceleration in erosion.</li>
                    <li><b>Decision signal:</b> Community and AI-support workflows should be reviewed before further automation is scaled.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='explanation-box' style='border-left-color: #A46B52;'>
                <h4 style='color: #A46B52 !important;'>💬 Latest verbatims analyzed</h4>
                <p>Five positive and five negative community messages are shown to keep the metric connected to real customer language, not only to the percentage trend.</p>
            </div>
            """, unsafe_allow_html=True)
            try:
                render_verbatim_cards(dados.get("reviews", pd.DataFrame()))
            except Exception as exc:
                st.warning(f"Could not render verbatims: {exc}")


# ---------------------------------------------------------
# 8. KPI 3
# ---------------------------------------------------------
elif aba == "⚡ KPI 3: SKU Anomaly":
    render_kpi_header(
        title="Unified SKU Anomaly Response Time",
        vsm="VSM: System 2 (Coordinating)",
        thrive="THRIVE: Sustains (E-Test)",
        what="Inventory shortages and dimensional sizing return variances that signal operational breakdowns.",
        decision="The system routes the alert: if inventory, Ops triggers replenishment; if fit, Merchandising pauses the AI Fit Predictor and launches a quality audit. <i>(Owner: Sam Whitaker)</i>",
        vanity="Game it by auto-closing alerts without resolving physical stock. <b>Guard-rail:</b> Pair with backorder limits and physical audits."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📦 Stockout Risk (Demand vs Forecast)")
        if "kpi3_all_sku" not in dados or dados["kpi3_all_sku"].empty:
            st.error("Inventory data was not loaded.")
        else:
            df = dados["kpi3_all_sku"].copy()
            sku = df["SKU_family"].astype(str).tolist()
            gaps = df["missing_units"].astype(float).tolist()
            colors = [COLOR_WARN if v > 0 else COLOR_SAFE for v in gaps]
            text = [f"{v:+,.0f} units" for v in gaps]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=gaps,
                y=sku,
                orientation="h",
                marker_color=colors,
                text=text,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="SKU family: %{y}<br>Demand - Forecast: %{x:+,.0f} units<extra></extra>",
                name="Demand - Forecast"
            ))
            fig.add_vline(x=0, line_color=COLOR_NEUTRAL, line_width=1)
            fig.update_layout(title="All SKU Families — Demand Above/Below Forecast", xaxis_title="Demand minus forecast units", yaxis_title="SKU family")
            max_abs = max(abs(min(gaps)), abs(max(gaps))) if gaps else 1
            fig.update_traces(textfont=dict(size=13))
            fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=True, zerolinecolor=COLOR_NEUTRAL, range=[-max_abs * 1.28, max_abs * 1.35])
            fig.update_yaxes(showgrid=False)
            fig = fig_layout(fig, height=620)
            fig.update_xaxes(showgrid=False, zeroline=True, zerolinecolor=COLOR_NEUTRAL, zerolinewidth=2)
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)

            source_sku = df[["SKU_family", "demand_units", "forecast_units", "missing_units", "status"]].rename(columns={
                "SKU_family": "SKU family",
                "demand_units": "Demand units",
                "forecast_units": "Forecast units",
                "missing_units": "Demand - forecast",
                "status": "Status"
            })
            show_source_table(source_sku, fmt={"Demand units": "{:,.0f}", "Forecast units": "{:,.0f}", "Demand - forecast": "{:+,.0f}"})

            attention = dados.get("kpi3_attention", pd.DataFrame()).copy()
            total_risk = attention["missing_units"].sum() if not attention.empty else 0
            st.markdown(f"""
            <div class='explanation-box'>
                <h4>🚨 Operational calculus</h4>
                <p>The chart uses <code>inventory_forecast.csv</code> and calculates <b>Demand Units - Forecast Units</b> for every SKU family.</p>
                <p><b>Color logic:</b> red bars = demand above forecast; green bars = forecast coverage was sufficient.</p>
                <p><b>Total positive stock pressure:</b> <b>{total_risk:,.0f}</b> units across <b>{len(attention)}</b> SKU families.</p>
            </div>
            """, unsafe_allow_html=True)
            render_stock_attention_board(attention)

    with col2:
        st.markdown("### 📏 Sizing Return Rate (%) by Size Band")
        if "kpi3_size" not in dados or dados["kpi3_size"].empty:
            st.error("Size-band return data was not loaded.")
        else:
            df = dados["kpi3_size"].copy()
            sizes = df["size_band"].astype(str).tolist()
            return_rates = df["return_rate_pct"].astype(float).tolist()
            shares = df["share_of_units_pct"].astype(float).tolist()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=sizes,
                y=return_rates,
                marker_color=COLOR_SAFE,
                text=[f"{v:.1f}%" for v in return_rates],
                textposition="outside",
                hovertemplate="Size: %{x}<br>Return rate: %{y:.1f}%<extra></extra>",
                name="Return rate (%)"
            ))
            fig.add_trace(go.Scatter(
                x=sizes,
                y=shares,
                yaxis="y2",
                mode="lines+markers+text",
                line=dict(width=3, color=COLOR_WARN),
                marker=dict(size=9, color=COLOR_WARN),
                text=[f"{v:.0f}%" for v in shares],
                textposition="top center",
                hovertemplate="Size: %{x}<br>Share of returned units: %{y:.1f}%<extra></extra>",
                name="Share of returned units (%)"
            ))
            fig.add_hline(y=23.0, line_dash="dash", line_color=COLOR_WARN, annotation_text="Danger threshold: 23%", annotation_position="top right")
            fig.update_layout(
                title="Return Rate by Size Band + Return Volume Distribution",
                xaxis_title="Size band",
                yaxis=dict(title="Return rate (%)", range=[0, max(35, max(return_rates) * 1.25)], ticksuffix="%", showgrid=False),
                yaxis2=dict(title="Share of returned units (%)", overlaying="y", side="right", range=[0, max(40, max(shares) * 1.25)], ticksuffix="%", showgrid=False),
            )
            fig.update_traces(textfont=dict(size=13))
            fig = fig_layout(fig, height=620)
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)
            fig.update_layout(yaxis2=dict(title="Share of returned units (%)", overlaying="y", side="right", range=[0, max(40, max(shares) * 1.25)], ticksuffix="%", showgrid=False, showline=True, linecolor="rgba(52,70,34,0.45)", tickfont=dict(size=14), title_font=dict(size=16)))
            st.plotly_chart(fig, use_container_width=True)

            source_size = df[["size_band", "share_of_units", "share_of_units_pct", "return_rate_pct"]].rename(columns={
                "size_band": "Size band",
                "share_of_units": "Share of units raw",
                "share_of_units_pct": "Share of returned units",
                "return_rate_pct": "Return rate"
            })
            show_source_table(source_size, fmt={"Share of units raw": "{:.2f}", "Share of returned units": "{:.1f}%", "Return rate": "{:.1f}%"})

            high_risk = df[df["return_rate_pct"] > 23]
            highest = df.sort_values("return_rate_pct", ascending=False).iloc[0]
            st.markdown(f"""
            <div class='safe-box'>
                <h4>✅ Sizing pattern calculus</h4>
                <p>The bars use <code>return_rate_pct</code> from <code>RETURN_RATE_BY_SIZE_BAND_YEAR2025.csv</code>. The line uses <code>share_of_units</code> from the same file, converted from raw share into percentage points.</p>
                <p><b>Highest risk size:</b> {highest['size_band']} at <b>{highest['return_rate_pct']:.1f}%</b>. <b>{len(high_risk)}</b> size bands exceed the 23% threshold.</p>
                <p><b>Decision:</b> pause or audit the AI Fit Predictor for bands above threshold, especially where return-rate risk and return-volume share overlap.</p>
            </div>
            """, unsafe_allow_html=True)
