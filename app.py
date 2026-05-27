import streamlit as st
import pandas as pd
from datetime import datetime
from db import load_data, save_data, load_expenses, save_expenses

st.set_page_config(page_title="Sublet SaaS", layout="wide")

df = load_data()
exp_df = load_expenses()

today = datetime.today()

# =========================
# STATUS ENGINE
# =========================
def status(row):
    if str(row["Status"]).lower() == "paid":
        return "Paid"
    elif pd.to_datetime(row["DueDate"]) < today:
        return "Overdue"
    return "Pending"

if not df.empty:
    df["PaymentStatus"] = df.apply(status, axis=1)

# =========================
# LOGIN
# =========================
st.sidebar.title("Login")
user = st.sidebar.text_input("Username")
pw = st.sidebar.text_input("Password", type="password")

if user != "admin" or pw != "admin123":
    st.warning("Login required")
    st.stop()

# =========================
# DASHBOARD
# =========================
st.title("🏢 Sublet SaaS System")

total = df["Rental"].sum() if not df.empty else 0
paid = df[df["Status"]=="Paid"]["Rental"].sum() if not df.empty else 0
outstanding = total - paid

total_expense = exp_df["Amount"].sum() if not exp_df.empty else 0
net_profit = total - total_expense

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Expected", f"RM {total}")
col2.metric("Collected", f"RM {paid}")
col3.metric("Expenses", f"RM {total_expense}")
col4.metric("Net Profit", f"RM {net_profit}")

st.divider()

# =========================
# ADD TENANT
# =========================
st.subheader("➕ Add Tenant")

with st.form("add"):
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

        df = pd.concat([df, new], ignore_index=True)
        save_data(df)
        st.success("Added")
        st.rerun()

# =========================
# MARK PAID
# =========================
st.subheader("💰 Mark Payment")

if not df.empty:
    t = st.selectbox("Tenant", df["TenantID"])

    if st.button("Mark as Paid"):
        df.loc[df["TenantID"] == t, "Status"] = "Paid"
        save_data(df)
        st.success("Updated")
        st.rerun()

# =========================
# EXPENSES MODULE
# =========================
st.divider()
st.subheader("💸 Expenses Tracker")

with st.form("expense_form"):
    date = st.date_input("Date")
    house = st.text_input("House")
    category = st.selectbox("Category", [
        "TNB",
        "Air Selangor",
        "WiFi",
        "Coway",
        "IWK",
        "Owner Payment",
        "Other"
    ])
    desc = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0)

    if st.form_submit_button("Add Expense"):
        new_exp = pd.DataFrame([{
            "Date": date,
            "House": house,
            "Category": category,
            "Description": desc,
            "Amount": amount
        }])

        exp_df = load_expenses()
        exp_df = pd.concat([exp_df, new_exp], ignore_index=True)
        save_expenses(exp_df)

        st.success("Expense added!")
        st.rerun()

# =========================
# EXPENSE SUMMARY
# =========================
st.subheader("📊 Expenses Summary")

exp_df = load_expenses()

if not exp_df.empty:
    st.metric("Total Expenses", f"RM {exp_df['Amount'].sum()}")
    st.dataframe(exp_df)
    st.bar_chart(exp_df.groupby("Category")["Amount"].sum())

# =========================
# TABLE
# =========================
st.divider()
st.subheader("Tenant List")
st.dataframe(df)

# =========================
# OVERDUE
# =========================
st.subheader("Overdue")
if not df.empty:
    st.dataframe(df[df["PaymentStatus"]=="Overdue"])