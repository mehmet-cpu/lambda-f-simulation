import json
import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# -----------------------------------------------------------------------------
# Sayfa Yapılandırması ve Başlık
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="λF Simulation Engine",
    page_icon="⚙️",
    layout="centered"
)
st.title("⚙️ λF Simulation & Data Entry Terminal")
st.caption("Use the controls in the sidebar to simulate market sentiment and see your simulation history below.")

# -----------------------------------------------------------------------------
# Firebase Bağlantısı (Cache'lenmiş)
# -----------------------------------------------------------------------------

if not firebase_admin._apps:
    secrets_dict = st.secrets["firebase_key"]
    firebase_creds_copy = dict(secrets_dict)
    firebase_creds_copy['private_key'] = firebase_creds_copy['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(firebase_creds_copy)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -----------------------------------------------------------------------------
# Simülasyon Kontrolleri (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.title("Simulation Controls")
try:
    with open('mock_data.json', 'r') as f:
        initial_topics = json.load(f)
except FileNotFoundError:
    st.error("`mock_data.json` dosyası bulunamadı.")
    st.stop()

simulation_inputs = {}
st.sidebar.header("Sentiment & Volume Parameters")
for topic in initial_topics:
    topic_name = topic["keyword"]
    st.sidebar.markdown(f"**{topic_name}**")
    sentiment_score = st.sidebar.slider(f"Sentiment Score", -1.0, 1.0, topic["sentiment_score"], 0.01, key=f"s_{topic_name}")
    tweet_count = st.sidebar.number_input(f"Tweet Volume", 0, None, topic["tweet_count"], 100, key=f"v_{topic_name}")
    simulation_inputs[topic_name] = {"sentiment": sentiment_score, "volume": tweet_count}
    st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# Hesaplama Motoru
# -----------------------------------------------------------------------------
def calculate_lambda_f(inputs):
    """Verilen girdilere göre Lambda-F skorunu hesaplar."""
    total_score, total_tweets = 0, 0
    for values in inputs.values():
        total_score += values["volume"] * values["sentiment"]
        total_tweets += values["volume"]
    avg_sentiment = total_score / total_tweets if total_tweets > 0 else 0
    lambda_f_score = min(max(avg_sentiment + 0.5, 0), 1)
    return avg_sentiment, lambda_f_score

avg_sentiment, lambda_F = calculate_lambda_f(simulation_inputs)

# -----------------------------------------------------------------------------
# Sonuçların Gösterimi (Ana Ekran)
# -----------------------------------------------------------------------------
st.header("📈 Simulation Results")
col1, col2 = st.columns(2)
col1.metric("Calculated Average Sentiment", f"{avg_sentiment:.4f}")
col2.metric("Resulting λF Score", f"{lambda_F:.4f}")

# ... (Durum mesajları aynı kalabilir)

# -----------------------------------------------------------------------------
# Veritabanına Kaydetme İşlemi
# -----------------------------------------------------------------------------
st.header("💾 Save to Database")
st.write("Click the button to save the current simulation result to the simulation history.")

if st.button("Save Current Simulation to History"):
    if db:
        # DEĞİŞİKLİK: Kayıt hedefi "lambda_f_simulation" olarak güncellendi
        collection_ref = db.collection("lambda_f_simulation")
        status = "Critical" if lambda_F > 0.7 else "Risky" if lambda_F > 0.5 else "Normal"
        doc_to_save = {
            "timestamp": firestore.SERVER_TIMESTAMP,
            "lambda_F": lambda_F,
            "status": status,
            "is_mock_data": True,
            "source_details": simulation_inputs
        }
        try:
            collection_ref.add(doc_to_save)
            st.success("Simulation saved successfully!")
            st.balloons()
            # YENİ: Anında güncelleme için cache temizleme ve yeniden çalıştırma
            st.cache_data.clear() # Geçmiş verileri tutan cache'i temizle
            st.rerun() # Sayfayı yeniden çalıştırarak listeyi güncelle
        except Exception as e:
            st.error(f"An error occurred while saving: {e}")
    else:
        st.error("Cannot save. Firebase connection is not available.")

st.markdown("---")

# -----------------------------------------------------------------------------
# YENİ BÖLÜM: Simülasyon Geçmişini Gösterme
# -----------------------------------------------------------------------------
st.header("📜 Simulation History")
st.write("Here are the latest simulations you have saved.")

# YENİ: Simülasyon geçmişini okuyan fonksiyon
@st.cache_data(ttl=3600) # Simülasyon geçmişini 1 saat cache'le
def fetch_simulation_history(_db_client):
    """`lambda_f_simulation` koleksiyonundan verileri çeker."""
    if _db_client is None: return pd.DataFrame()
    try:
        # DEĞİŞİKLİK: "lambda_f_simulation" koleksiyonundan okuma
        docs = _db_client.collection("lambda_f_simulation").order_by("timestamp", direction="DESCENDING").limit(10).stream()
        data = [doc.to_dict() for doc in docs]
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"Error fetching simulation history: {e}")
        return pd.DataFrame()

# Veriyi çek ve göster
df_sim_history = fetch_simulation_history(db)

if not df_sim_history.empty:
    # Geçmişi bir grafik olarak göster
    st.line_chart(df_sim_history.rename(columns={'lambda_F': 'λF Score'}).set_index('timestamp')['λF Score'])

    # Detaylı veriyi bir tablo olarak göster
    st.write("Latest Records:")
    st.dataframe(
        df_sim_history[['timestamp', 'lambda_F', 'status']],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No simulation history found. Save a simulation to see it here.")
