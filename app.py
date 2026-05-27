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
.block-container { padding: 1.8rem 2.2rem; }

section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #1f2937;
}

h1,h2,h3 { color:#e5e7eb; }

.kpi {
    background: linear-gradient(145deg,#0f172a,#0b1220);
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
}

.kpi-value { font-size:22px; font-weight:700; color:#fff; }

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
        return "Pending"
    except:
        return "Pending"

if not df.empty:
    df["PaymentStatus"] = df.apply(status, axis=1)

# =========================
# LOGIN
# =========================
st.sidebar.title("🏢 Sublet SaaS Pro MAX")

user = st.sidebar.text_input("User")
pw = st.sidebar.text_input("Pass", type="password")

if user != "admin" or pw != "admin123":
    st.stop()

# =========================
# DEFAULT HOUSES
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

existing_houses = df["House"].dropna().unique().tolist()
houses = sorted(list(set(default_houses + existing_houses)))

# =========================
# ADD HOUSE (REAL SAVE)
# =========================
st.sidebar.markdown("### 🏘️ Houses")

new_house = st.sidebar.text_input("Add new house")

if st.sidebar.button("➕ Add House"):
    if new_house:
        if new_house not in houses:
            houses.append(new_house)

        # add dummy row so house exists in DB
        new_row = pd.DataFrame([{
            "TenantID": "",
            "Name": "",
            "House": new_house,
            "Room": "",
            "Rental": 0,
            "DueDate": today,
            "Status": "Unpaid"
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)

        st.sidebar.success("House added")

# =========================
# NAVIGATION
# =========================
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Tenant", "Expenses", "Reports"] + houses
)

selected_house = page if page in houses else None

# =========================
# FILTER DATA
# =========================
if selected_house:
    df_view = df[df["House"] == selected_house].copy()
    exp_view = exp_df[exp_df["House"] == selected_house].copy()
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
        <div style="color:#94a3b8;font-size:12px">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if page == "Dashboard":
    st.title("🏠 Dashboard")

    total_income = df["Rental"].sum() if not df.empty else 0
    expenses = exp_df["Amount"].sum() if not exp_df.empty else 0

    c1,c2,c3 = st.columns(3)
    kpi("Income", f"RM {total_income:,.0f}")
    kpi("Expenses", f"RM {expenses:,.0f}")
    kpi("Profit", f"RM {total_income-expenses:,.0f}")

    st.markdown("---")
    st.subheader("🏘️ House Overview")
    st.dataframe(df, use_container_width=True)

# =========================
# HOUSE PAGE (NOTION STYLE)
# =========================
elif selected_house:
    st.title(f"🏘️ {selected_house}")

    st.subheader("👥 Tenants (Inline Edit)")

    edited_df = st.data_editor(
        df_view,
        num_rows="dynamic",
        use_container_width=True,
        key="tenant_editor"
    )

    if st.button("💾 Save Tenant Changes"):
        # replace only house rows
        df = df[df["House"] != selected_house]
        df = pd.concat([df, edited_df], ignore_index=True)
        save_data(df)
        st.success("Saved")

    st.markdown("---")

    st.subheader("💸 Expenses (Inline Edit)")

    edited_exp = st.data_editor(
        exp_view,
        num_rows="dynamic",
        use_container_width=True,
        key="expense_editor"
    )

    if st.button("💾 Save Expense Changes"):
        exp_df = exp_df[exp_df["House"] != selected_house]
        exp_df = pd.concat([exp_df, edited_exp], ignore_index=True)
        save_expenses(exp_df)
        st.success("Saved")

# =========================
# TENANT PAGE
# =========================
elif page == "Tenant":
    st.title("👥 All Tenants")
    st.data_editor(df, num_rows="dynamic", use_container_width=True)

# =========================
# EXPENSES PAGE
# =========================
elif page == "Expenses":
    st.title("💸 Expenses")
    st.data_editor(exp_df, num_rows="dynamic", use_container_width=True)

# =========================
# REPORTS
# =========================
elif page == "Reports":
    st.title("📊 Reports")

    st.dataframe(df)
    st.dataframe(exp_df)