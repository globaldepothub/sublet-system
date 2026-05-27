import streamlit as st
import pandas as pd
from datetime import datetime
from db import load_data, save_data, load_expenses, save_expenses

st.set_page_config(page_title="Sublet SaaS Pro", layout="wide")

# =========================
# SAAS UI STYLE
# =========================
st.markdown("""
<style>

/* Background */
.main {
    background-color: #0b1220;
}

/* Hide Streamlit default padding */
.block-container {
    padding: 2rem 2.5rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f172a;
}

/* Titles */
h1, h2, h3 {
    color: #e2e8f0;
}

/* Card */
.saas-card {
    background: #111827;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    border: 1px solid #1f2937;
}

/* KPI Card */
.kpi {
    background: linear-gradient(135deg, #111827, #0f172a);
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #1f2937;
    text-align: center;
}

/* KPI label */
.kpi-label {
    font-size: 13px;
    color: #94a3b8;
}

/* KPI value */
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
}

/* Divider */
hr {
    border: 1px solid #1f2937;
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
st.sidebar.markdown("## 🔐 Admin Panel")

user = st.sidebar.text_input("Username")
pw = st.sidebar.text_input("Password", type="password")

if user != "admin" or pw != "admin123":
    st.stop()

st.sidebar.markdown("---")

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Navigation", [
    "🏠 Dashboard",
    "👥 Tenant",
    "💸 Expenses",
    "📊 Reports"
])

# =========================
# FILTER
# =========================
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
# KPI CARD FUNCTION
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
if menu == "🏠 Dashboard":

    st.title("🏢 Sublet SaaS Dashboard")

    total_income = df_view["Rental"].sum() if not df_view.empty else 0
    collected = df_view[df_view["Status"] == "Paid"]["Rental"].sum() if not df_view.empty else 0
    expenses = exp_view["Amount"].sum() if not exp_view.empty else 0
    profit = total_income - expenses

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi("Income", f"RM {total_income:,.2f}")
    with col2:
        kpi("Collected", f"RM {collected:,.2f}")
    with col3:
        kpi("Expenses", f"RM {expenses:,.2f}")
    with col4:
        kpi("Net Profit", f"RM {profit:,.2f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # =========================
    # CHART
    # =========================
    st.subheader("📊 Profit Analytics")

    if not df_view.empty:

        income_by_house = df_view.groupby("House")["Rental"].sum()
        expense_by_house = exp_view.groupby("House")["Amount"].sum() if not exp_view.empty else pd.Series(dtype=float)

        chart_df = pd.DataFrame({
            "Income": income_by_house,
            "Expenses": expense_by_house
        }).fillna(0)

        chart_df["Profit"] = chart_df["Income"] - chart_df["Expenses"]

        st.bar_chart(chart_df)

    st.markdown("<hr>", unsafe_allow_html=True)

    # =========================
    # OVERDUE
    # =========================
    st.subheader("🚨 Overdue Alerts")

    overdue = df_view[df_view["PaymentStatus"] == "Overdue"] if not df_view.empty else pd.DataFrame()

    if not overdue.empty:
        st.error(f"{len(overdue)} tenants overdue")
        st.dataframe(overdue, use_container_width=True)
    else:
        st.success("All tenants are up to date")

# =========================
# TENANT
# =========================
elif menu == "👥 Tenant":

    st.title("👥 Tenant Management")

    with st.expander("➕ Add Tenant", expanded=False):

        with st.form("tenant_form"):
            tid = st.text_input("Tenant ID")
            name = st.text_input("Name")
            house = st.text_input("House")
            room = st.text_input("Room")
            rental = st.number_input("Rental", min_value=0.0)
            due = st.date_input("Due Date")
            status_input = st.selectbox("Status", ["Paid", "Unpaid"])

            submit = st.form_submit_button("Save Tenant")

            if submit:
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

                st.success("Tenant added")
                st.rerun()

    st.markdown("### Tenant List")
    st.dataframe(df_view, use_container_width=True)

# =========================
# EXPENSES
# =========================
elif menu == "💸 Expenses":

    st.title("💸 Expenses Tracker")

    with st.expander("➕ Add Expense", expanded=False):

        with st.form("exp_form"):
            date = st.date_input("Date")
            house = st.text_input("House")
            category = st.selectbox("Category", [
                "TNB", "Air Selangor", "WiFi", "Coway", "IWK", "Owner Payment", "Other"
            ])
            desc = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.0)

            submit = st.form_submit_button("Save Expense")

            if submit:
                new = pd.DataFrame([{
                    "Date": date,
                    "House": house,
                    "Category": category,
                    "Description": desc,
                    "Amount": amount
                }])

                exp2 = pd.concat([exp_df, new], ignore_index=True)
                save_expenses(exp2)

                st.success("Expense added")
                st.rerun()

    st.markdown("### Expense Data")
    st.dataframe(exp_view, use_container_width=True)

    st.subheader("📊 Category Breakdown")
    if not exp_view.empty:
        st.bar_chart(exp_view.groupby("Category")["Amount"].sum())

# =========================
# REPORTS
# =========================
elif menu == "📊 Reports":

    st.title("📊 Monthly Reports")

    if not df.empty:
        month_list = pd.to_datetime(df["DueDate"]).dt.month.dropna().unique().tolist()
        month = st.selectbox("Select Month", sorted(month_list))
    else:
        month = None

    if month:

        monthly_df = df[pd.to_datetime(df["DueDate"]).dt.month == month]
        monthly_exp = exp_df[pd.to_datetime(exp_df["Date"]).dt.month == month] if not exp_df.empty else pd.DataFrame()

        income = monthly_df["Rental"].sum()
        expense = monthly_exp["Amount"].sum() if not monthly_exp.empty else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            kpi("Income", f"RM {income:,.2f}")
        with col2:
            kpi("Expenses", f"RM {expense:,.2f}")
        with col3:
            kpi("Profit", f"RM {(income - expense):,.2f}")

        st.markdown("<hr>", unsafe_allow_html=True)

        st.subheader("Tenant Report")
        st.dataframe(monthly_df, use_container_width=True)

        st.subheader("Expense Breakdown")
        if not monthly_exp.empty:
            st.bar_chart(monthly_exp.groupby("Category")["Amount"].sum())