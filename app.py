import streamlit as st
import pandas as pd
from datetime import datetime
from db import load_data, save_data, load_expenses, save_expenses

st.set_page_config(page_title="Sublet SaaS Pro MAX", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.main { background: #0a0f1c; }
.block-container { padding: 1rem 1rem; }

section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #1f2937;
}

h1,h2,h3 { color:#e5e7eb; }

.kpi {
    background: linear-gradient(145deg,#0f172a,#0b1220);
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 12px;
    text-align: center;
}

.kpi-value { font-size:20px; font-weight:700; color:#fff; }

hr { border:1px solid #1f2937; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
df = load_data()
exp_df = load_expenses()
today = datetime.today()

if df is None:
    df = pd.DataFrame()

if exp_df is None:
    exp_df = pd.DataFrame()

if "House" not in df.columns:
    df["House"] = ""

# =========================
# STATUS ENGINE
# =========================
def status(row):
    try:
        if str(row.get("Status","")).lower() == "paid":
            return "Paid"
        elif pd.to_datetime(row["DueDate"]) < today:
            return "Overdue"
        return "Unpaid"
    except:
        return "Unpaid"

if not df.empty:
    df["PaymentStatus"] = df.apply(status, axis=1)

# =========================
# LOGIN
# =========================
st.sidebar.title("🏢 SaaS MAX")

user = st.sidebar.text_input("User")
pw = st.sidebar.text_input("Pass", type="password")

if user != "admin" or pw != "admin123":
    st.stop()

# =========================
# HOUSE SYSTEM
# =========================
default_houses = [
    "BSS",
    "PUNCAK 7 17-06",
    "PUNCAK 7 21-05",
    "PUNCAK 7 09-07",
    "KRISTAL VIEW B-12-9",
    "MUTIARA ANGGERIK A-4-1",
    "PRIMA U1 1-21-8",
    "ALAM SANJUNG A-16-11"
]

houses = sorted(list(set(default_houses + df["House"].dropna().tolist())))

# =========================
# NAVIGATION
# =========================
page = st.sidebar.selectbox("Navigation", ["Dashboard", "Reports", "Houses"])

selected_house = None

if page == "Houses":
    selected_house = st.sidebar.selectbox("Select House", houses)

# =========================
# FILTER DATA
# =========================
if selected_house:
    df_view = df[df["House"] == selected_house].copy()
    exp_view = exp_df.copy()
else:
    df_view = df.copy()
    exp_view = exp_df.copy()

if not df_view.empty:
    df_view["PaymentStatus"] = df_view.apply(status, axis=1)

# =========================
# KPI
# =========================
def kpi(label, value):
    st.markdown(f"""
    <div class="kpi">
        <div style="color:#94a3b8;font-size:11px">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    st.title("🏠 Dashboard")

    income = df["Rental"].sum() if not df.empty else 0
    expense = exp_df["Amount"].sum() if not exp_df.empty else 0

    c1, c2, c3 = st.columns(3)
    kpi("Income", f"RM {income:,.0f}")
    kpi("Expenses", f"RM {expense:,.0f}")
    kpi("Profit", f"RM {income-expense:,.0f}")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

# =========================
# HOUSE PAGE
# =========================
elif selected_house:
    st.title(f"🏘️ {selected_house}")

    # =========================
    # TENANTS
    # =========================
    st.subheader("👥 Tenants")

    df_clean = df_view.drop(columns=["House"], errors="ignore")

    edited_df = st.data_editor(
        df_clean,
        num_rows="dynamic",
        use_container_width=True,
        key="tenant_editor",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Paid", "Unpaid"],
                required=True
            )
        }
    )

    if st.button("💾 Save Tenants"):
        edited_df["House"] = selected_house

        df = df[df["House"] != selected_house]
        df = pd.concat([df, edited_df], ignore_index=True)

        df["Status"] = df["Status"].apply(
            lambda x: "Paid" if str(x).lower() == "paid" else "Unpaid"
        )

        save_data(df)
        st.success("Saved")
        st.rerun()

    st.markdown("---")

    # =========================
    # EXPENSES (CLEAN 3 COLUMNS ONLY)
    # =========================
    st.subheader("💸 Expenses")

    CATEGORY_OPTIONS = [
        "TNB",
        "IWK",
        "RENTAL",
        "AIR SELANGORKU",
        "WIFI",
        "COWAY",
        "OTHER EXPENSES"
    ]

    exp_clean = exp_view.copy()

    if "Category" not in exp_clean.columns:
        exp_clean["Category"] = "OTHER EXPENSES"
    if "Amount" not in exp_clean.columns:
        exp_clean["Amount"] = 0
    if "Status" not in exp_clean.columns:
        exp_clean["Status"] = "Unpaid"

    # FORCE ONLY 3 COLUMNS
    exp_clean = exp_clean[["Category", "Amount", "Status"]]

    edited_exp = st.data_editor(
        exp_clean,
        num_rows="dynamic",
        use_container_width=True,
        key="expense_editor",
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORY_OPTIONS,
                required=True
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Paid", "Unpaid"],
                required=True
            )
        }
    )

    if st.button("💾 Save Expenses"):
        exp_df = edited_exp.copy()

        exp_df["Status"] = exp_df["Status"].apply(
            lambda x: "Paid" if str(x).lower() == "paid" else "Unpaid"
        )

        save_expenses(exp_df)
        st.success("Saved")
        st.rerun()

# =========================
# REPORTS
# =========================
elif page == "Reports":
    st.title("📊 Reports")

    st.dataframe(df, use_container_width=True)
    st.dataframe(exp_df, use_container_width=True)