from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///data/sublet.db")

# =========================
# INIT TABLE (RUN ON FIRST TIME)
# =========================
def init_db():
    df = pd.DataFrame(columns=[
        "TenantID","Name","House","Room","Rental","DueDate","Status"
    ])
    df.to_sql("tenants", engine, if_exists="replace", index=False)

# =========================
# LOAD DATA
# =========================
def load_data():
    return pd.read_sql("tenants", engine)

# =========================
# SAVE DATA
# =========================
def save_data(df):
    df.to_sql("tenants", engine, if_exists="replace", index=False)