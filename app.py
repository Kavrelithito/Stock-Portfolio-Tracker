import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

DB_FILE = "portfolio.db"

# ---------- Database Setup ----------
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT,
        symbol TEXT,
        action TEXT,
        quantity REAL,
        price REAL,
        mero_transfer TEXT DEFAULT 'No',
        notes TEXT
    )
""")
conn.commit()

# Ensure mero_transfer column exists
cols = [col[1] for col in c.execute("PRAGMA table_info(portfolio)")]
if "mero_transfer" not in cols:
    c.execute("ALTER TABLE portfolio ADD COLUMN mero_transfer TEXT DEFAULT 'No'")
    conn.commit()

# ---------- Functions ----------
def get_trades():
    return pd.read_sql("SELECT * FROM portfolio ORDER BY entry_date DESC", conn)

def add_trade(entry_date, symbol, action, quantity, price, mero_transfer, notes):
    c.execute("""
        INSERT INTO portfolio (entry_date, symbol, action, quantity, price, mero_transfer, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entry_date, symbol, action, quantity, price, mero_transfer, notes))
    conn.commit()

def highlight_no(val):
    if str(val).strip().lower() == "no":
        return "background-color: red; color: white"
    return ""

# ---------- App ----------
st.title("📈 Stock Portfolio Tracker")

# --- Trade Entry Form ---
with st.form("trade_form", clear_on_submit=True):
    entry_date = st.date_input("Date", value=date.today())
    symbol = st.text_input("Symbol (e.g., AAPL, MSFT)")
    action = st.selectbox("Action", ["Buy", "Sell"])
    quantity = st.text_input("Quantity")  # Blank default
    price = st.text_input("Price")        # Blank default
    mero_transfer = st.selectbox("Transferred from MeroShare?", ["No", "Yes"], index=0)
    notes = st.text_area("Notes")
    
    submitted = st.form_submit_button("Add Trade")
    if submitted:
        q = float(quantity) if quantity else None
        p = float(price) if price else None
        add_trade(entry_date, symbol, action, q, p, mero_transfer, notes)
        st.success("✅ Trade added!")

# --- Current Holdings ---
st.subheader("📊 Current Holdings")
df = get_trades()
if not df.empty:
    # Only calculate if quantity column has values
    if "quantity" in df.columns:
        holdings = (
            df.groupby(["symbol", "action"])["quantity"]
            .sum()
            .unstack(fill_value=0)
        )
        holdings["Net"] = holdings.get("Buy", 0) - holdings.get("Sell", 0)
        st.dataframe(holdings)
    else:
        st.info("No quantity data available to calculate holdings.")
else:
    st.info("No trades yet.")

# --- Trade History ---
st.subheader("📜 Trade History")
if not df.empty:
    if "mero_transfer" in df.columns:
        st.dataframe(df.style.applymap(highlight_no, subset=["mero_transfer"]))
    else:
        st.dataframe(df)
else:
    st.info("No trade history available.")
