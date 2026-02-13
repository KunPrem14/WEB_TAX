import streamlit as st
import pandas as pd
from db_utils import *

init_db()

st.set_page_config(
    page_title="Tax Management System",
    page_icon="💰",
    layout="wide"
)

st.title("💼 TAX Automatically")
st.caption("Accounting System")

left, right = st.columns([4, 1])

with right:
    st.subheader("📌 MENU")
    menu = st.radio(
        "",
        [
            "Dashboard",
            "Adding Customer",
            "Search",
            "Update Tax Status",
            "Delete Customer",
            "Import Excel",
            "Export Excel",
            "Calculate Tax"
        ]
    )

with left:
    st.image(
        "assets/logo.png",
        width=256
    )
    st.markdown("## TAX Automatically")
    st.caption("Accounting System")
    
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background-color: #f5f7fa;
    border-radius: 12px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- ADD ----------------
if menu == "Adding Customer":
    st.subheader("➕ Add Customer")

    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            job = st.text_input("Job")
            income = st.number_input("Income per month", min_value=0.0)
        with col2:
            surname = st.text_input("Surname")
            expense = st.number_input("Expense per month", min_value=0.0)

        submitted = st.form_submit_button("Submit")

    if submitted:
        cid = generate_customer_id()
        income_y = income * 12
        expense_y = expense * 12
        tax_income = income_y - expense_y
        tax = cal_tax(tax_income)

        cur.execute("""
        INSERT INTO Customer_Info VALUES(?,?,?,?,?,?)
        """, (cid, name, surname, job, income, expense))

        cur.execute("""
        INSERT INTO TAX_SUMMARY
        (ID_Customer, Income_year, Expense_year, Tax_income, Tax_amount, Status)
        VALUES (?,?,?,?,?,?)
        """, (cid, income_y, expense_y, tax_income, tax, 1))

        conn.commit()
        st.success(f"Successfully added customer (ID: {cid})")

# ---------------- SEARCH ----------------
elif menu == "Search":
    st.subheader("🔍 Search Customer")
    cid = st.text_input("Customer ID")

    if st.button("Search"):
        cur.execute("""
        SELECT c.ID_Customer, c.NAME, c.SURNAME, c.JOB,
               t.Income_year, t.Expense_year, t.Tax_amount, t.Status
        FROM Customer_Info c
        JOIN TAX_SUMMARY t ON c.ID_Customer = t.ID_Customer
        WHERE c.ID_Customer=?
        """, (cid,))
        data = cur.fetchone()

        if not data:
            st.error("Not found customer ID")
        else:
            st.info("Customer Details")
            st.json({
                "ID": data[0],
                "Name": f"{data[1]} {data[2]}",
                "Job": data[3],
                "Income per year": data[4],
                "Expense per year": data[5],
                "Tax": data[6],
                "Status": status_text(data[7])
            })

# ---------------- UPDATE ----------------
elif menu == "Update Tax Status":
    st.subheader("✏️ Update Tax Status")
    cid = st.text_input("Customer ID")
    status = st.selectbox(
        "Status",
        [(1, "NOT_SUBMITTED"), (2, "IN_PROGRESS"), (3, "COMPLETED")],
        format_func=lambda x: x[1]
    )

    if st.button("Update"):
        cur.execute("""
        UPDATE TAX_SUMMARY SET Status=?
        WHERE ID_Customer=?
        """, (status[0], cid))
        conn.commit()
        st.success("Successfully updated status")

# ---------------- DELETE ----------------
elif menu == "Delete Customer":
    st.subheader("🗑️ Delete Customer")
    cid = st.text_input("Customer ID")

    if st.button("Delete"):
        cur.execute("DELETE FROM TAX_SUMMARY WHERE ID_Customer=?", (cid,))
        cur.execute("DELETE FROM Customer_Info WHERE ID_Customer=?", (cid,))
        conn.commit()
        st.warning("Successfully deleted customer data")

# ---------------- IMPORT ----------------
elif menu == "Import Excel":
    st.subheader("📥 Import Excel")
    file = st.file_uploader("Choose Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(
            file,
            sheet_name="ข้อมูลบุคคล",
            engine="openpyxl"
        )
        st.dataframe(df)

        if st.button("Import Data"):
            for _, row in df.iterrows():
                cid = generate_customer_id()
                income_m = row["Income per month"]
                expense_m = row["Expense per month"]

                income_y = income_m * 12
                expense_y = expense_m * 12
                tax_income = income_y - expense_y
                tax = cal_tax(tax_income)

                cur.execute(
                    "INSERT INTO Customer_Info VALUES (?,?,?,?,?,?)",
                    (cid, row["ชื่อ"], row["นามสกุล"], row["อาชีพ"], income_m, expense_m)
                )
                cur.execute(
                    """INSERT INTO TAX_SUMMARY
                    (ID_Customer, Income_year, Expense_year, Tax_income, Tax_amount, Status)
                    VALUES (?,?,?,?,?,1)
                    """,
                    (cid, income_y, expense_y, tax_income, tax)
                )

            conn.commit()
            st.success("Import data completed")

# ---------------- EXPORT ----------------
elif menu == "Export Excel":
    st.subheader("📤 Export Excel")

    df = pd.read_sql_query("""
    SELECT
        c.ID_Customer AS รหัส,
        c.NAME AS ชื่อ,
        c.SURNAME AS นามสกุล,
        c.JOB AS อาชีพ,
        c.Income_month AS รายได้ต่อเดือน,
        c.Expense_month AS ค่าใช้จ่ายต่อเดือน,
        t.Tax_amount AS ภาษี,
        t.Status AS สถานะ
    FROM Customer_Info c
    JOIN TAX_SUMMARY t ON c.ID_Customer = t.ID_Customer
    """, conn)

    df["สถานะ"] = df["สถานะ"].apply(status_text)
    st.dataframe(df)

    from io import BytesIO

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="ข้อมูลภาษี", index=False)

    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="tax_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- CAL TAX ----------------
elif menu == "Calculate Tax":
    st.subheader("🧮 Calculate Tax")
    income = st.number_input("Income per month", min_value=0.0)
    expense = st.number_input("Expense per month", min_value=0.0)

    if st.button("Calculate"):
        tax_income = (income - expense) * 12
        tax = cal_tax(tax_income)
        st.metric("Tax per year", f"{tax:,.2f} Baht")
        st.metric("Tax per month", f"{tax/12:,.2f} Baht")

if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    df = pd.read_sql_query("""
        SELECT
            c.ID_Customer,
            c.NAME || ' ' || c.SURNAME AS fullname,
            t.Tax_amount,
            t.Status
        FROM Customer_Info c
        JOIN TAX_SUMMARY t ON c.ID_Customer = t.ID_Customer
    """, conn)

    if df.empty:
        st.warning("No data available. Please add customers first.")
        st.stop()

    # ===== KPI =====
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Customer", len(df))
    col2.metric("💰 TAX", f"{df['Tax_amount'].sum():,.2f}")
    col3.metric("✅ COMPLETED", (df["Status"] == 3).sum())
    col4.metric("⏳ IN_PROGRESS", (df["Status"] == 2).sum())

    st.divider()

    # ===== STATUS CHART =====
    status_df = df["Status"].value_counts().reset_index()
    status_df.columns = ["Status", "จำนวน"]
    status_df["Status"] = status_df["Status"].apply(status_text)

    st.subheader("📌 Status Chart")
    st.bar_chart(status_df.set_index("Status"))

    st.divider()

    # ===== TABLE =====
    st.subheader("🧾 List of Customers")
    show_df = df.copy()
    show_df["Status"] = show_df["Status"].apply(status_text)

    st.dataframe(show_df, use_container_width=True)


