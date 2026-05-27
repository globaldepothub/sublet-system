from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///data/sublet.db")

# =========================
# TABLE SCHEMAS (CENTRALIZED)
# =========================
TENANT_COLUMNS = [
    "TenantID","Name","House","Room","Rental","DueDate","Status"
]

EXPENSE_COLUMNS = [
    "Date","House","Category","Description","Amount"
]

# =========================
# INIT TENANTS TABLE
# =========================
def init_db():
    df = pd.DataFrame(columns=TENANT_COLUMNS)
    df.to_sql("tenants", engine, if_exists="replace", index=False)

# =========================
# LOAD TENANTS (SAFE)
# =========================
def load_data():
    try:
        df = pd.read_sql("tenants", engine)
        return df
    except:
        df = pd.DataFrame(columns=TENANT_COLUMNS)
        df.to_sql("tenants", engine, if_exists="replace", index=False)
        return df

# =========================
# SAVE TENANTS
# =========================
def save_data(df):
    df.to_sql("tenants", engine, if_exists="replace", index=False)

# =========================
# INIT EXPENSES TABLE
# =========================
def init_expenses():
    df = pd.DataFrame(columns=EXPENSE_COLUMNS)
    df.to_sql("expenses", engine, if_exists="replace", index=False)

# =========================
# LOAD EXPENSES (SAFE)
# =========================
def load_expenses():
    try:
        df = pd.read_sql("expenses", engine)
        return df
    except:
        df = pd.DataFrame(columns=EXPENSE_COLUMNS)
        df.to_sql("expenses", engine, if_exists="replace", index=False)
        return df

# =========================
# SAVE EXPENSES
# =========================
def save_expenses(df):
    df.to_sql("expenses", engine, if_exists="replace", index=False)