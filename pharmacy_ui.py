import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import requests
from urllib.parse import quote_plus

# ---------- DB CONNECTION (SQLAlchemy) ----------
DB_CONFIG = {
    "dbname": "pharmacy",
    "user": "postgres",
    "password": "p@55w0rd",  # replace with your actual password
    "host": "localhost",
    "port": "5432"
}

@st.cache_resource
def get_engine():
    # Encode password safely for connection string
    encoded_pwd = quote_plus(DB_CONFIG["password"])
    conn_str = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{encoded_pwd}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(conn_str)

@st.cache_data
def run_query(query: str):
    engine = get_engine()
    df = pd.read_sql(query, engine)
    return df

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Pharmacy Dashboard", layout="wide")
st.title("💊 Pharmacy BI Dashboard")
st.markdown("A professional interactive dashboard for pharmacy operations")

# ---------- AI Assistant (Flicker-Free, No JS) ----------
import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000/ask"
DEFAULT_DB = "pharmacy"

# --- CSS ---
st.markdown("""
    <style>
    /* Make sidebar 45% width */
    [data-testid="stSidebar"] {
        width: 45% !important;
        min-width: 45% !important;
        transform: translateX(0) !important;
        visibility: visible !important;
        opacity: 1 !important;
        transition: all 0.3s ease;
    }

    /* Hide ALL Streamlit sidebar toggle arrows (both visible & ghost ones) */
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapsedControl"], 
    div[data-testid="stSidebarNavCollapseButton"], 
    section[data-testid="stSidebar"] > div:first-child > div:first-child {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Ensure main area fills rest of the space */
    section[data-testid="stSidebar"] + section.main {
        width: calc(100% - 45%) !important;
        transition: width 0.3s ease;
    }

    /* Floating AI Assistant button */
    .assistant-btn {
        position: fixed;
        top: 75px;
        right: 20px;
        background-color: #1565c0;
        color: white;
        border: none;
        border-radius: 25px;
        padding: 8px 18px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    .assistant-btn:hover {
        background-color: #0d47a1;
        transform: scale(1.05);
    }

    /* Hide hidden form wrapper */
    div[data-testid="stForm"] {
        display: none !important;
    }

    /* Hide top "collapsed" icon when sidebar open */
    [data-testid="stSidebarContent"] + div {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize state ---
if "assistant_open" not in st.session_state:
    st.session_state.assistant_open = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Toggle logic ---
toggle_key = "assistant_toggle"
if toggle_key not in st.session_state:
    st.session_state[toggle_key] = False

def toggle_assistant():
    st.session_state.assistant_open = not st.session_state.assistant_open

# --- Floating AI Assistant button ---
button_label = "❌ Close Assistant" if st.session_state.assistant_open else "🤖 AI Assistant"
st.button(
    button_label,
    key="assistant_btn",
    on_click=toggle_assistant,
    help="Click to toggle AI Assistant panel",
)

# Apply floating style to the button
st.markdown("""
    <style>
    div[data-testid="stButton"][data-testid="stButton"]:has(button#assistant_btn) {
        position: fixed !important;
        top: 75px !important;
        right: 20px !important;
        z-index: 1000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Chat Panel ---
if st.session_state.assistant_open:
    st.sidebar.title("🤖 Pharmacy Assistant")
    st.sidebar.markdown("Ask questions about your pharmacy data below:")

    for role, msg in st.session_state.chat_history:
        if role == "user":
            st.sidebar.markdown(f"🧑‍💼 **You:** {msg}")
        else:
            st.sidebar.markdown(f"🤖 **Assistant:** {msg}")

    user_input = st.sidebar.text_input("Your question:", key="chat_input")

    if st.sidebar.button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append(("user", user_input))
            try:
                with st.spinner("Assistant is thinking..."):
                    response = requests.post(
                        f"{FASTAPI_URL}?db_name={DEFAULT_DB}",
                        json={"question": user_input},
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "❌ No answer received.")
                    else:
                        answer = f"⚠️ Error: {response.status_code} - {response.text}"
            except Exception as e:
                answer = f"💥 Connection error: {e}"

            st.session_state.chat_history.append(("assistant", answer))
            st.rerun()



# ---------- KPIs ----------
col1, col2, col3 = st.columns(3)

total_sales = run_query("""
    SELECT SUM(s.quantity * m.price_per_unit) AS revenue
    FROM sales s JOIN medicines m ON s.medicine_id = m.medicine_id;
""")["revenue"][0]

total_units = run_query("SELECT SUM(quantity) as units FROM sales;")["units"][0]

active_customers = run_query("""
    SELECT COUNT(DISTINCT customer_id) as custs
    FROM sales
    WHERE sale_date > CURRENT_DATE - INTERVAL '180 days';
""")["custs"][0]

with col1:
    fig = go.Figure(go.Indicator(
        mode="number",
        value=total_sales,
        title={"text": "Total Revenue"},
        number={"prefix": "₹ ", "valueformat": ",.0f"}
    ))
    fig.update_layout(height=200, margin=dict(t=20, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure(go.Indicator(
        mode="number",
        value=total_units,
        title={"text": "Units Sold"},
        number={"valueformat": ",d"}
    ))
    fig.update_layout(height=200, margin=dict(t=20, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    fig = go.Figure(go.Indicator(
        mode="number",
        value=active_customers,
        title={"text": "Active Customers (6m)"},
        number={"valueformat": ",d"}
    ))
    fig.update_layout(height=200, margin=dict(t=20, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

# ---------- Sales Overview ----------
st.subheader("📈 Sales Overview")
col1, col2 = st.columns(2)

with col1:
    sales_trend = run_query("""
        SELECT DATE_TRUNC('quarter', sale_date) AS quarter,
               SUM(s.quantity*m.price_per_unit) AS revenue
        FROM sales s JOIN medicines m ON s.medicine_id = m.medicine_id
        GROUP BY 1 ORDER BY 1;
    """)
    sales_trend["quarter_label"] = [
        f"Q{((d.month-1)//3)+1} {d.year}" for d in sales_trend["quarter"]
    ]

    fig = px.bar(
        sales_trend, x="quarter_label", y="revenue",
        text="revenue", color="revenue", color_continuous_scale="Blues",
        labels={"quarter_label": "Quarter", "revenue": "Revenue (₹)"},
        title="Quarterly Sales Revenue"
    )
    fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig.update_layout(xaxis_tickangle=-45, title_x=0.5, height=250, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_meds = run_query("""
        SELECT m.name, SUM(s.quantity*m.price_per_unit) as revenue
        FROM sales s JOIN medicines m ON s.medicine_id = m.medicine_id
        GROUP BY m.name ORDER BY revenue DESC LIMIT 10;
    """)
    fig2 = px.bar(
        top_meds, x="revenue", y="name", orientation="h",
        text="revenue", color="revenue", color_continuous_scale="Viridis",
        labels={"name": "Medicine", "revenue": "Revenue (₹)"},
        title="Top 10 Medicines by Revenue"
    )
    fig2.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig2.update_layout(yaxis=dict(autorange="reversed"), title_x=0.5, height=250, coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ---------- Inventory ----------
st.subheader("📦 Inventory: Low Stock Items")
low_stock = run_query("""
    SELECT m.name, i.stock_qty, i.expiry_date
    FROM inventory i
    JOIN medicines m ON i.medicine_id = m.medicine_id
    WHERE i.stock_qty < 50
    ORDER BY i.stock_qty ASC
    LIMIT 10;
""")
fig3 = px.bar(
    low_stock, x="stock_qty", y="name", orientation="h",
    text="stock_qty", color="stock_qty", color_continuous_scale="Reds",
    labels={"name": "Medicine", "stock_qty": "Stock Qty"}
)
fig3.update_traces(texttemplate="%{text}", textposition="outside")
fig3.update_layout(yaxis=dict(autorange="reversed"), title_x=0.5, height=300, coloraxis_showscale=False)
st.plotly_chart(fig3, use_container_width=True)

# ---------- Expiry Risk ----------
st.subheader("⏳ Medicines Near Expiry (Next 90 Days)")
near_expiry = run_query("""
    SELECT m.name, i.batch_no, i.expiry_date, i.stock_qty
    FROM inventory i
    JOIN medicines m ON i.medicine_id = m.medicine_id
    WHERE i.expiry_date < CURRENT_DATE + INTERVAL '90 days'
    ORDER BY i.expiry_date;
""")
st.dataframe(near_expiry)

# ---------- Customers ----------
st.subheader("👥 Top Customers by Spend")
top_customers = run_query("""
    SELECT c.name, SUM(s.quantity*m.price_per_unit) as spend
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN medicines m ON s.medicine_id = m.medicine_id
    GROUP BY c.name ORDER BY spend DESC LIMIT 5;
""")
fig4 = px.bar(
    top_customers, x="spend", y="name", orientation="h",
    text="spend", color="spend", color_continuous_scale="Teal",
    labels={"name": "Customer", "spend": "Spend (₹)"}
)
fig4.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
fig4.update_layout(yaxis=dict(autorange="reversed"), title_x=0.5, height=300, coloraxis_showscale=False)
st.plotly_chart(fig4, use_container_width=True)
