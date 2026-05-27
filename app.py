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

df = df.drop(columns=["TenantID"], errors="ignore")

# =========================
# SAFE NUMERIC FIX (CRITICAL)
# =========================
df["Rental"] = pd.to_numeric(df.get("Rental", 0), errors="coerce").fillna(0)

# =========================
# EXPENSE CLEAN (HOUSE IS KEY FIX)
# =========================
def clean_expenses(df_in):
    df = df_in.copy()

    if "House" not in df.columns:
        df["House"] = ""

    for col in ["Category", "Amount", "Status"]:
        if col not in df.columns:
            df[col] = "OTHER EXPENSES" if col=="Category" else 0 if col=="Amount" else "Unpaid"

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Status"] = df["Status"].apply(lambda x: "Paid" if str(x).lower()=="paid" else "Unpaid")

    return df[["House","Category","Amount","Status"]]

exp_df = clean_expenses(exp_df)

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
    "BSS","PUNCAK 7 17-06","PUNCAK 7 21-05","PUNCAK 7 09-07",
    "KRISTAL VIEW B-12-9","MUTIARA ANGGERIK A-4-1",
    "PRIMA U1 1-21-8","ALAM SANJUNG A-16-11"
]

houses = sorted(list(set(default_houses + df["House"].dropna().tolist())))

page = st.sidebar.selectbox("Navigation", ["Dashboard", "Reports", "Houses"])

selected_house = None
if page == "Houses":
    selected_house = st.sidebar.selectbox("Select House", houses)

# =========================
# FILTER DATA
# =========================
if selected_house:
    df_view = df[df["House"] == selected_house].copy()
    exp_view = exp_df[exp_df["House"] == selected_house].copy()
else:
    df_view = df.copy()
    exp_view = exp_df.copy()

# =========================
# KPI SAFE FIX
# =========================
def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0

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

    income = safe_float(df["Rental"].sum())
    expense = safe_float(exp_df["Amount"].sum())
    profit = income - expense

    c1,c2,c3 = st.columns(3)
    kpi("Income", f"RM {income:,.0f}")
    kpi("Expenses", f"RM {expense:,.0f}")
    kpi("Profit", f"RM {profit:,.0f}")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

# =========================
# HOUSE PAGE
# =========================
elif selected_house:
    st.title(f"🏘️ {selected_house}")

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
                options=["Paid","Unpaid"]
            )
        }
    )

    if st.button("💾 Save Tenants"):
        edited_df["House"] = selected_house

        df_all = df[df["House"] != selected_house]
        df_all = pd.concat([df_all, edited_df], ignore_index=True)

        save_data(df_all)
        st.success("Saved")
        st.rerun()

    st.markdown("---")

    st.subheader("💸 Expenses")

    CATEGORY_OPTIONS = [
        "TNB","IWK","RENTAL",
        "AIR SELANGORKU","WIFI",
        "COWAY","OTHER EXPENSES"
    ]

    edited_exp = st.data_editor(
        exp_view,
        num_rows="dynamic",
        use_container_width=True,
        key="expense_editor",
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORY_OPTIONS
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Paid","Unpaid"]
            )
        }
    )

    if st.button("💾 Save Expenses"):
        edited_exp["House"] = selected_house   # 🔥 IMPORTANT FIX

        exp_all = exp_df[exp_df["House"] != selected_house]
        exp_all = pd.concat([exp_all, edited_exp], ignore_index=True)

        save_expenses(exp_all)
        st.success("Saved")
        st.rerun()

# =========================
# REPORTS
# =========================
elif page == "Reports":
    st.title("📊 Reports")

    st.subheader("👥 Tenants Report")
    st.dataframe(df, use_container_width=True)

    st.subheader("💸 Expenses Report")
    st.dataframe(exp_df, use_container_width=True)

    st.subheader("📊 Summary")

    income = safe_float(df["Rental"].sum())
    expense = safe_float(exp_df["Amount"].sum())
    profit = income - expense

    st.metric("Income", f"RM {income:,.0f}")
    st.metric("Expenses", f"RM {expense:,.0f}")
    st.metric("Profit", f"RM {profit:,.0f}")