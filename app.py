import streamlit as st
import pandas as pd
from datetime import datetime
from db import load_data, save_data, load_expenses, save_expenses
st.set_page_config(page_title="Sublet SaaS Pro", layout="wide")
# =========================
# PREMIUM SAAS STYLE
# =========================
st.markdown("""
<style>
/* Background */
.main {
    background: #0a0f1c;
}
/* Layout padding */
.block-container {
    padding: 1.8rem 2.2rem;
}
/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0b1220;
    border-right: 1px solid #1f2937;
}
/* Text */
h1, h2, h3 {
    color: #e5e7eb;
}
/* KPI Card */
.kpi {
    background: linear-gradient(145deg, #0f172a, #0b1220);
    border: 1px solid #1f2937;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
}
/* KPI hover */
.kpi:hover {
    transform: translateY(-2px);
    transition: 0.2s ease;
}
/* KPI text */
.kpi-label {
    font-size: 12px;
    color: #94a3b8;
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
}
/* Section divider */
hr {
    border: 1px solid #1f2937;
}
/* Table radius */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)
# =========================
# LOAD DATA
# =========================
df = load_data()
exp_df = load_expenses()
today = datetime.today()
# =========================
# SAFE STATUS ENGINE
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
st.sidebar.markdown("## 🏢 Sublet SaaS Pro")
st.sidebar.caption("Admin Dashboard")
user = st.sidebar.text_input("Username")
pw = st.sidebar.text_input("Password", type="password")
if user != "admin" or pw != "admin123":
    st.stop()
st.sidebar.markdown("---")
# =========================
# NAVIGATION
# =========================
menu = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Tenant",
    "Expenses",
    "Reports"
])
houses = df["House"].dropna().unique().tolist() if not df.empty else []
house_filter = st.sidebar.multiselect("Filter House", houses)
if house_filter:
    df_view = df[df["House"].isin(house_filter)].copy()
    exp_view = exp_df[exp_df["House"].isin(house_filter)].copy()
else:
    df_view = df.copy()
    exp_view = exp_df.copy()
if not df_view.empty:
    df_view["PaymentStatus"] = df_view.apply(status, axis=1)
# =========================
# KPI COMPONENT
# =========================
def kpi(label, value):
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)
# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.title("🏠 Dashboard")
    st.caption("Overview of rental performance, expenses and profit")
    total_income = df_view["Rental"].sum() if not df_view.empty else 0
    collected = df_view[df_view["Status"] == "Paid"]["Rental"].sum() if not df_view.empty else 0
    expenses = exp_view["Amount"].sum() if not exp_view.empty else 0
    profit = total_income - expenses
    # KPI ROW
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Income", f"RM {total_income:,.0f}")
    with c2:
        kpi("Collected", f"RM {collected:,.0f}")
    with c3:
        kpi("Expenses", f"RM {expenses:,.0f}")
    with c4:
        kpi("Net Profit", f"RM {profit:,.0f}")
    st.markdown("<hr>", unsafe_allow_html=True)
    # MAIN GRID
    left, right = st.columns([2.2, 1])
    with left:
        st.subheader("📊 Profit Overview")
        if not df_view.empty:
            income_by_house = df_view.groupby("House")["Rental"].sum()
            expense_by_house = exp_view.groupby("House")["Amount"].sum() if not exp_view.empty else pd.Series(dtype=float)
            chart_df = pd.DataFrame({
                "Income": income_by_house,
                "Expenses": expense_by_house
            }).fillna(0)
            chart_df["Profit"] = chart_df["Income"] - chart_df["Expenses"]
            st.bar_chart(chart_df)
        else:
            st.info("No data available")
    with right:
        st.subheader("🚨 Overdue")
        overdue = df_view[df_view["PaymentStatus"] == "Overdue"] if not df_view.empty else pd.DataFrame()
        if not overdue.empty:
            st.error(f"{len(overdue)} overdue tenants")
            st.dataframe(overdue, use_container_width=True)
        else:
            st.success("All clear")
# =========================
# TENANT
# =========================
elif menu == "Tenant":
    st.title("👥 Tenant Management")
    with st.expander("➕ Add Tenant"):
        with st.form("tenant_form"):
            tid = st.text_input("Tenant ID")
            name = st.text_input("Name")
            house = st.text_input("House")
            room = st.text_input("Room")
            rental = st.number_input("Rental", min_value=0.0)
            due = st.date_input("Due Date")
            status_input = st.selectbox("Status", ["Paid", "Unpaid"])
            if st.form_submit_button("Save"):
                new = pd.DataFrame([{
                    "TenantID": tid,
                    "Name": name,
                    "House": house,
                    "Room": room,
                    "Rental": rental,
                    "DueDate": due,
                    "Status": status_input
                }])
                df2 = pd.concat([df, new], ignore_index=True)
                save_data(df2)
                st.success("Saved")
                st.rerun()
    st.dataframe(df_view, use_container_width=True)
# =========================
# EXPENSES
# =========================
elif menu == "Expenses":
    st.title("💸 Expenses Tracker")
    with st.expander("➕ Add Expense"):
        with st.form("expense_form"):
            date = st.date_input("Date")
            house = st.text_input("House")
            category = st.selectbox("Category", [
                "TNB", "Air Selangor", "WiFi", "Coway", "IWK", "Owner Payment", "Other"
            ])
            desc = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.0)
            if st.form_submit_button("Save"):
                new = pd.DataFrame([{
                    "Date": date,
                    "House": house,
                    "Category": category,
                    "Description": desc,
                    "Amount": amount
                }])
                exp2 = pd.concat([exp_df, new], ignore_index=True)
                save_expenses(exp2)
                st.success("Saved")
                st.rerun()
    st.dataframe(exp_view, use_container_width=True)
    st.subheader("📊 Breakdown")
    if not exp_view.empty:
        st.bar_chart(exp_view.groupby("Category")["Amount"].sum())
# =========================
# REPORTS (SAAS STYLE TABS)
# =========================
elif menu == "Reports":
    st.title("📊 Reports")
    if not df.empty:
        month_list = pd.to_datetime(df["DueDate"], errors="coerce").dt.month.dropna().unique().tolist()
        month = st.selectbox("Select Month", sorted(month_list))
    else:
        month = None
    if month:
        monthly_df = df[pd.to_datetime(df["DueDate"], errors="coerce").dt.month == month]
        monthly_exp = exp_df[pd.to_datetime(exp_df["Date"], errors="coerce").dt.month == month] if not exp_df.empty else pd.DataFrame()
        income = monthly_df["Rental"].sum()
        expense = monthly_exp["Amount"].sum() if not monthly_exp.empty else 0
        c1, c2, c3 = st.columns(3)
        kpi("Income", f"RM {income:,.0f}")
        kpi("Expenses", f"RM {expense:,.0f}")
        kpi("Profit", f"RM {income-expense:,.0f}")
        st.markdown("<hr>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Tenant Report", "Expense Breakdown"])
        with tab1:
            st.dataframe(monthly_df, use_container_width=True)
        with tab2:
            if not monthly_exp.empty:
                st.bar_chart(monthly_exp.groupby("Category")["Amount"].sum())