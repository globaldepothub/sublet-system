from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///data/sublet.db")

# =========================
# INIT TENANTS TABLE
# =========================
def init_db():
    df = pd.DataFrame(columns=[
        "TenantID","Name","House","Room","Rental","DueDate","Status"
    ])
    df.to_sql("tenants", engine, if_exists="replace", index=False)

# =========================
# LOAD TENANTS DATA (SAFE)
# =========================
def load_data():
    try:
        return pd.read_sql("tenants", engine)
    except:
        df = pd.DataFrame(columns=[
            "TenantID","Name","House","Room","Rental","DueDate","Status"
        ])
        df.to_sql("tenants", engine, if_exists="replace", index=False)
        return df

# =========================
# SAVE TENANTS DATA
# =========================
def save_data(df):
    df.to_sql("tenants", engine, if_exists="replace", index=False)

# =========================
# INIT EXPENSES TABLE
# =========================
def init_expenses():
    df = pd.DataFrame(columns=[
        "Date",
        "House",
        "Category",
        "Description",
        "Amount"
    ])
    df.to_sql("expenses", engine, if_exists="replace", index=False)

# =========================
# LOAD EXPENSES DATA (SAFE)
# =========================
def load_expenses():
    try:
        return pd.read_sql("expenses", engine)
    except:
        df = pd.DataFrame(columns=[
            "Date",
            "House",
            "Category",
            "Description",
            "Amount"
        ])
        df.to_sql("expenses", engine, if_exists="replace", index=False)
        return df

# =========================
# SAVE EXPENSES DATA (MISSING BEFORE)
# =========================
def save_expenses(df):
    df.to_sql("expenses", engine, if_exists="replace", index=False)