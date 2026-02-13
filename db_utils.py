import sqlite3

conn = sqlite3.connect("Perada_Prototype.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Customer_Info (
        ID_Customer TEXT PRIMARY KEY,
        NAME TEXT,
        SURNAME TEXT,
        JOB TEXT,
        Income_month REAL,
        Expense_month REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS TAX_SUMMARY (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_Customer TEXT,
        Income_year REAL,
        Expense_year REAL,
        Tax_income REAL,
        Tax_amount REAL,
        Status INTEGER
    )
    """)
    conn.commit()

def generate_customer_id():
    cur.execute("""
        SELECT MAX(CAST(SUBSTR(ID_Customer,2) AS INTEGER))
        FROM Customer_Info
    """)
    last_id = cur.fetchone()[0]
    if last_id is None:
        return "P001"
    return f"P{last_id + 1:03d}"

def status_text(status):
    return {
        1: "NOT_SUBMITTED",
        2: "IN_PROGRESS",
        3: "COMPLETED"
    }.get(status, "UNKNOWN")

def cal_tax(net_income):
    if net_income <= 150000:
        return 0
    elif net_income <= 300000:
        return (net_income -150000) * 0.05
    elif net_income <= 500000:
        return (net_income - 300000) * 0.10 + 7500
    elif net_income <= 750000:
        return (net_income - 500000) * 0.15 + 27500
    elif net_income <= 1000000:
        return (net_income - 750000) * 0.20 + 65000
    elif net_income <=2000000:
        return (net_income - 1000000) * 0.25 + 115000
    elif net_income <= 5000000:
        return (net_income - 2000000 ) * 0.30 + 365000
    else:
        return (net_income - 5000000 ) * 0.35 + 1265000
