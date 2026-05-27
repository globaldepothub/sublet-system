import streamlit as st
import pandas as pd
from datetime import datetime
from db import load_data, save_data, load_expenses, save_expenses

st.set_page_config(page_title="Sublet SaaS Pro", layout="wide")

df = load_data()
exp_df = load_expenses()

today = datetime.today()

# =========================
# STATUS ENGINE
# =========================
def status(row):
    try:
        if str(row["Status"]).lower() == "paid":
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
st.sidebar.title("🔐 Login")
user = st.sidebar.text_input("Username")
pw = st.sidebar.text_input("Password", type="password")

if user != "admin" or pw != "admin123":
    st.stop()

# =========================
# MENU
# =========================
menu = st.sidebar.selectbox("📌 Menu", [
    "🏠 Dashboard",
    "👥 Tenant",
    "💸 Expenses",
    "📊 Monthly Report"
])

# =========================
# HOUSE FILTER (GLOBAL)
# =========================
houses = df["House"].dropna().unique().tolist() if not df.empty else []
house_filter = st.sidebar.multiselect("🏘️ Filter House", houses)

if house_filter:
    df_view = df[df["House"].isin(house_filter)]
    exp_view = exp_df[exp_df["House"].isin(house_filter)]
else:
    df_view = df
    exp_view = exp_df

# =========================
# DASHBOARD
# =========================
if menu == "🏠 Dashboard":

    st.title("🏢 Sublet SaaS Pro Dashboard")

    total_income = df_view["Rental"].sum() if not df_view.empty else 0
    collected = df_view[df_view["Status"]=="Paid"]["Rental"].sum() if not df_view.empty else 0
    expenses = exp_view["Amount"].sum() if not exp_view.empty else 0
    profit = total_income - expenses

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Income", f"RM {total_income}")
    col2.metric("Collected", f"RM {collected}")
    col3.metric("Expenses", f"RM {expenses}")
    col4.metric("Net Profit", f"RM {profit}")

    st.divider()

    # 📈 Profit chart per house
    st.subheader("📈 Profit Per House")

    if not df_view.empty:
        income_by_house = df_view.groupby("House")["Rental"].sum()
        expense_by_house = exp_view.groupby("House")["Amount"].sum() if not exp_view.empty else 0

        chart_df = pd.DataFrame({
            "Income": income_by_house,
            "Expenses": exp_view.groupby("House")["Amount"].sum() if not exp_view.empty else 0
        }).fillna(0)

        chart_df["Profit"] = chart_df["Income"] - chart_df["Expenses"]

        st.bar_chart(chart_df[["Income","Expenses","Profit"]])

    # 🔔 Overdue alert
    st.subheader("🔔 Overdue Alerts")

    overdue = df_view[df_view["PaymentStatus"]=="Overdue"]
    if not overdue.empty:
        st.error(f"{len(overdue)} tenants overdue!")
        st.dataframe(overdue)
    else:
        st.success("No overdue tenants 🎉")

# =========================
# TENANT PAGE
# =========================
elif menu == "👥 Tenant":

    st.title("👥 Tenant Management")

    with st.form("add_tenant"):
        tid = st.text_input("Tenant ID")
        name = st.text_input("Name")
        house = st.text_input("House")
        room = st.text_input("Room")
        rental = st.number_input("Rental", min_value=0)
        due = st.date_input("Due Date")
        status_input = st.selectbox("Status", ["Paid","Unpaid"])

        if st.form_submit_button("Add"):
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
            st.success("Added")
            st.rerun()

    st.dataframe(df_view, use_container_width=True)

# =========================
# EXPENSES PAGE
# =========================
elif menu == "💸 Expenses":

    st.title("💸 Expenses")

    with st.form("expense"):
        date = st.date_input("Date")
        house = st.text_input("House")
        category = st.selectbox("Category", [
            "TNB","Air Selangor","WiFi","Coway","IWK","Owner Payment","Other"
        ])
        desc = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0)

        if st.form_submit_button("Add"):
            new = pd.DataFrame([{
                "Date": date,
                "House": house,
                "Category": category,
                "Description": desc,
                "Amount": amount
            }])

            exp2 = pd.concat([exp_df, new], ignore_index=True)
            save_expenses(exp2)
            st.success("Added")
            st.rerun()

    st.dataframe(exp_view, use_container_width=True)

    st.subheader("📊 Breakdown")
    if not exp_view.empty:
        st.bar_chart(exp_view.groupby("Category")["Amount"].sum())

# =========================
# MONTHLY REPORT
# =========================
elif menu == "📊 Monthly Report":

    st.title("📊 Monthly Report")

    month = st.selectbox("Select Month", pd.to_datetime(df["DueDate"]).dt.month.unique() if not df.empty else [])

    if month and not df.empty:

        monthly_df = df[pd.to_datetime(df["DueDate"]).dt.month == month]
        monthly_exp = exp_df[pd.to_datetime(exp_df["Date"]).dt.month == month] if not exp_df.empty else pd.DataFrame()

        income = monthly_df["Rental"].sum()
        expense = monthly_exp["Amount"].sum() if not monthly_exp.empty else 0

        st.metric("Monthly Income", f"RM {income}")
        st.metric("Monthly Expenses", f"RM {expense}")
        st.metric("Monthly Profit", f"RM {income - expense}")

        st.subheader("Tenant Performance")
        st.dataframe(monthly_df)

        st.subheader("Expenses Breakdown")
        if not monthly_exp.empty:
            st.bar_chart(monthly_exp.groupby("Category")["Amount"].sum())

        # 📄 Export Excel button
        excel_data = pd.ExcelWriter("monthly_report.xlsx", engine="openpyxl")

        monthly_df.to_excel(excel_data, sheet_name="Tenants", index=False)
        monthly_exp.to_excel(excel_data, sheet_name="Expenses", index=False)

        excel_data.close()

        with open("monthly_report.xlsx", "rb") as f:
            st.download_button(
                "📄 Download Excel Report",
                f,
                file_name="monthly_report.xlsx"
            )