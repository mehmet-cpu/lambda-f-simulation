import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime



# Mock veri yükleyici
def load_mock_data(file_path='mock_data.json'):
    with open(file_path, 'r') as f:
        return json.load(f)


use_mock = True

if use_mock:
    data = load_mock_data()
    total_score = 0
    for topic in data:
        tweet_count = topic["tweet_count"]
        sentiment = topic["sentiment_score"]
        total_score += tweet_count * sentiment

    avg_sentiment = total_score / sum(d["tweet_count"] for d in data)
else:
    # Burada gerçek API çağrıları yer alacak
    pass

# Lambda-F değeri hesapla
lambda_F = min(max(avg_sentiment + 0.5, 0), 1)  # -0.5 ile +0.5 arası sentiment için 0-1 normalize

# Streamlit dashboard kodu
st.title("λF Indicator Simulation")
st.write("Observe potential breaking points in the financial system with λF Simulation.")
st.warning("⚠️ ATTENTION: This is an interactive simulation of our Lambda-F engine. It does not provide real-time trading recommendations. This tool is designed to demonstrate how our model responds to changes in market sentiment and how it can identify ‘phase transitions’.")
st.write(f"Average Sentiment Score: {avg_sentiment:.3f}")
st.write(f"Current λF Value: `{lambda_F:.3f}`")
if lambda_F > 0.7:
    st.error("🚨 Critical: The market may be overheated.")
elif lambda_F > 0.5:
    st.warning("⚠️ The risk of volatility is increasing.")
else:
    st.success("✅ Normal")




# Sabit veri
sentiment_data = {
    'Varlık': ['Bitcoin', 'GME', 'LUNA'],
    'Sentiment Skoru': [0.2, -0.1, 0.5]
}

lambda_F_data = {
    'Varlık': ['Bitcoin', 'GME', 'LUNA'],
    'λF Value': [0.6, 0.4, 0.72]
}

df_sentiment = pd.DataFrame(sentiment_data)
df_lambda_F = pd.DataFrame(lambda_F_data)

st.set_page_config(layout="wide")
st.title('Lambda-F Risk Indicator 🔍')
st.markdown('## Emotion Score and λF Risk Analysis')

col1, col2 = st.columns(2)

with col1:
    st.markdown('### 💬 Sentiment Scores')
    fig1, ax1 = plt.subplots()
    ax1.bar(df_sentiment['Varlık'], df_sentiment['Sentiment Skoru'], color='skyblue')
    ax1.set_ylim([-1, 1])
    ax1.axhline(0, color='gray', linestyle='--')
    ax1.set_ylabel('Sentiment Skoru')
    st.pyplot(fig1)

with col2:
    st.markdown('### 🔺 λF Values')
    fig2, ax2 = plt.subplots()
    bars = ax2.bar(df_lambda_F['Varlık'], df_lambda_F['λF Value'], color='orange')
    ax2.axhline(0.7, color='red', linestyle='--', label='Critical Threshold (0.7)')
    ax2.axhline(0.5, color='darkorange', linestyle='--', label='Warning Threshold (0.5)')
    ax2.set_ylim([0, 1])
    ax2.set_ylabel('λF Value')
    ax2.legend()
    st.pyplot(fig2)


st.markdown("---")
st.subheader("📊 λF Values for the Last 7 Days (Time Series)")




dates = pd.date_range(end=pd.Timestamp.today(), periods=7)
lambdaF_data = {
    "Bitcoin": [0.32, 0.35, 0.45, 0.52, 0.58, 0.62, lambda_F],  # Bugünkü lambda_F değeri sona eklendi
    "GME":     [0.28, 0.31, 0.37, 0.49, 0.66, 0.71, 0.68],
    "LUNA":    [0.30, 0.33, 0.40, 0.51, 0.59, 0.63, 0.69]
}
df_lambdaF = pd.DataFrame(lambdaF_data, index=dates)

# Grafiği çiz
fig, ax = plt.subplots(figsize=(10, 5))
for asset in df_lambdaF.columns:
    ax.plot(df_lambdaF.index, df_lambdaF[asset], label=asset, marker='o')

# Kritik eşikleri çiz
ax.axhline(y=0.5, color='orange', linestyle='--', label='⚠️ Risk Threshold')
ax.axhline(y=0.7, color='red', linestyle='--', label='🚨 Danger Threshold')

# Stil ve etiketler
ax.set_title("λF Time Series (7 Days)", fontsize=14)
ax.set_xlabel("Time")
ax.set_ylabel("λF Value")
ax.legend()
ax.grid(True)

# Streamlit’e çizdir
st.pyplot(fig)


if not firebase_admin._apps:
    secrets_dict = st.secrets["firebase_key"]

    firebase_creds_copy = dict(secrets_dict)

    firebase_creds_copy['private_key'] = firebase_creds_copy['private_key'].replace('\\n', '\n')

    cred = credentials.Certificate(firebase_creds_copy)
    firebase_admin.initialize_app(cred)

db = firestore.client()




def fetch_lambdaF_history():
    db = firestore.client()
    docs = db.collection("lambdaF").order_by("timestamp").stream()
    
    data = []
    for doc in docs:
        doc_data = doc.to_dict()
        data.append({
            "timestamp": doc_data.get("timestamp"),
            "lambda_F": doc_data.get("lambda_F")
        })
    
    df = pd.DataFrame(data)
    df = df.dropna()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


st.subheader("🕰️ Lambda-F Time Series Graph")

df_history = fetch_lambdaF_history()

if not df_history.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_history["timestamp"], df_history["lambda_F"], marker='o', label="λF", color='blue')
    ax.axhline(y=0.7, color='red', linestyle='--', label="Kritik Eşik")
    ax.set_title("λF Value Time Series")
    ax.set_xlabel("Time")
    ax.set_ylabel("λF")
    ax.legend()
    st.pyplot(fig)
else:
    st.warning("No historical data available yet.")


if lambda_F > 0.7:
    st.error(f"🚨 Critical Area: λF = {lambda_F:.3f} — Social unrest is high. Be careful!")
elif lambda_F > 0.5:
    st.warning(f"⚠️ Fluctuation Risk: λF = {lambda_F:.3f} — Uncertainty is growing.")
else:
    st.success(f"✅ Normal Level: λF = {lambda_F:.3f} — The market is calm.")

status = "Kritik" if lambda_F > 0.7 else "Riskli" if lambda_F > 0.5 else "Normal"


from firebase_reader import get_lambda_f_data

st.set_page_config(page_title="Lambda-F Dashboard", layout="centered")

st.title("📊 Lambda-F Scores (Live from Firebase)")
st.caption("Flux Finance - Daily λF score monitoring tool")

try:
    df = get_lambda_f_data()
    if df.empty:
        st.warning("No data yet. Daily data may not have been written to Firebase.")
    else:
        # Tarihi sıralayalım
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by="timestamp")

        st.subheader("📈 Lambda-F Scores Time Series")
        fig, ax = plt.subplots()
        ax.plot(df['timestamp'], df['lambda_F'], marker='o')
        ax.axhline(y=0.7, color='red', linestyle='--', label="Critical Level")
        ax.axhline(y=0.5, color='orange', linestyle='--', label="Risk Level")
        ax.set_ylabel("λF Score")
        ax.set_xlabel("Time")
        ax.legend()
        st.pyplot(fig)

        st.subheader("📄 VData Table")
        st.dataframe(df)

except Exception as e:
    st.error(f"An error occurred while retrieving data: {e}")

