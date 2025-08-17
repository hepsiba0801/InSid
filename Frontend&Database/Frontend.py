import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io
from sqlalchemy import create_engine
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Insider Threat Dashboard", page_icon="🚨", layout="wide")

# ---------- LOAD DATA ----------
df = pd.read_csv("insider_threat_results.csv")

# ---------- TITLE ----------
st.markdown("<h1 style='text-align:center; color:#FF4B4B;'>Insider Threat Monitoring</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---------- FILTER CHECKBOX ----------
st.sidebar.header("⚙️ Filters")

show_suspicious = st.sidebar.checkbox("Show Suspicious", value=True)
show_insider = st.sidebar.checkbox("Show Insider", value=True)

filters = []
if show_suspicious:
    filters.append("suspicious")
if show_insider:
    filters.append("insider")

if filters:
    df_filtered = df[df["anomaly_flag"].isin(filters)]
else:
    df_filtered = pd.DataFrame(columns=df.columns)  # Empty if none selected

# ---------- METRICS ----------
col1, col2 = st.columns(2)
with col1:
    suspicious_count = df[df["anomaly_flag"] == "suspicious"].shape[0]
    st.metric("Suspicious Users", suspicious_count)
with col2:
    insider_count = df[df["anomaly_flag"] == "insider"].shape[0]
    st.metric("Insider Users", insider_count)

st.markdown("---")

# ---------- TABLE ----------
st.subheader("🔍 Suspicious & Insider Users")
if not df_filtered.empty:
    st.dataframe(df_filtered)
else:
    st.warning("⚠️ No users match the selected filters.")

# ---------- CHARTS ----------
st.subheader("📊 Anomaly Distribution")

col3, col4 = st.columns(2)

with col3:
    if not df_filtered.empty:
        st.bar_chart(df_filtered["anomaly_flag"].value_counts())
    else:
        st.info("No data to display.")

with col4:
    if "safe_score" in df_filtered.columns and not df_filtered.empty:
        if "user" in df_filtered.columns:
            st.line_chart(df_filtered.set_index("user")["safe_score"])
        else:
            st.line_chart(df_filtered["safe_score"])

# ---------- CLOUD DATABASE FUNCTION ----------
def save_to_cloud_db(df_report):
    try:
        db_url = "postgresql://hepsiba:YlQ0bqaJTKny5OvkSBfR0LRzNEnfyKtS@dpg-d2g8landiees73d7mcb0-a.singapore-postgres.render.com/insid"
        engine = create_engine(db_url)

        # Append suspicious/insider data into the table
        df_report.to_sql("insider_threat_results", engine, if_exists="append", index=False)

        return True
    except Exception as e:
        st.error(f"❌ Failed to save data to cloud DB: {e}")
        return False

# ---------- EMAIL FUNCTION ----------
def send_report_via_email(df_report, suspicious_count, insider_count):
    sender_email = "heheheheleo@gmail.com"       # <-- change this
    sender_password = "xrpxwgnbxueohqrr"         # <-- your Gmail App Password
    recipient = "7140hepsiba@gmail.com"          # <-- fixed recipient email

    subject = "Insider Threat Report"
    body = f"""
    Hello,

    Please find attached the latest suspicious & insider users report.

    Total Suspicious: {suspicious_count}
    Total Insider: {insider_count}

    Regards,
    Insider Threat Monitoring System
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, "plain"))

    # CSV as attachment
    csv_buffer = io.StringIO()
    df_report.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_buffer.getvalue().encode())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="insider_report.csv"')
    msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Failed to send email: {e}")
        return False

# ---------- SEND EMAIL BUTTON ----------
st.markdown("---")
if st.button("📧 Save & Send Report"):
    if not df_filtered.empty:
        # Step 1: Save to cloud DB
        db_success = save_to_cloud_db(df_filtered)

        # Step 2: Send email only if DB upload worked
        if db_success:
            email_success = send_report_via_email(df_filtered, suspicious_count, insider_count)

            # ✅ Final success message
            if email_success:
                st.success("✅ Data successfully uploaded to cloud DB AND email report sent!")
                st.info(f"📅 Last successful operation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("⚠️ No suspicious or insider data available to send.")
