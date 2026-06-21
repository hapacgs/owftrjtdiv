import streamlit as st
import pandas as pd
from pymongo import MongoClient

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Freight Data Pro", page_icon="🚀", layout="centered")

# --- CUSTOM CSS FOR GLOWING UI ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    /* Buttons with Glow */
    div.stButton > button {
        background-color: #00ffcc !important;
        color: #000000 !important;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        box-shadow: 0 0 15px #00ffcc80;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        box-shadow: 0 0 25px #00ffcc;
        transform: scale(1.02);
    }
    /* File Uploader Customization */
    .stFileUploader {
        border: 2px dashed #444;
        border-radius: 10px;
        padding: 10px;
    }
    /* Subheaders */
    h1, h2, h3 { color: #00ffcc !important; }
    </style>
""", unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
MONGO_URI = st.secrets["MONGO_URI"]

@st.cache_resource
def get_db_connection():
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client['OWDATA_RJT_DIV']

db = get_db_connection()
collection = db['owdata_csv_file']

# --- APP LAYOUT ---
st.title("🚀 Outward Freight Pro")
st.markdown("Professional data pipeline for FOIS portal exports.")
st.divider()

uploaded_file = st.file_uploader("Upload your FOIS CSV file", type="csv")

if uploaded_file is not None:
    try:
        # File Processing
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        
        # --- Cleaning Logic ---
        df = df.dropna(how='all')
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        df = df[df['DVSN'].notna()]
        df = df.drop_duplicates()

        st.subheader("Data Preview")
        # Creating a metric for visibility
        col1, col2 = st.columns([1, 2])
        col1.metric("Cleaned Rows", len(df))
        
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Save to Database"):
            if not df.empty:
                with st.spinner('Syncing to Cloud...'):
                    # Duplicate check based on RR NUMBER
                    rr_numbers = df['RR NUMBER'].tolist()
                    existing_docs = collection.find({"RR NUMBER": {"$in": rr_numbers}}, {"RR NUMBER": 1})
                    existing_rrs = [doc['RR NUMBER'] for doc in existing_docs]
                    
                    new_data = df[~df['RR NUMBER'].isin(existing_rrs)]
                    
                    if not new_data.empty:
                        collection.insert_many(new_data.to_dict("records"))
                        st.success(f"Success! {len(new_data)} new records added.")
                        if len(df) > len(new_data):
                            st.warning(f"{len(df) - len(new_data)} duplicates were ignored.")
                    else:
                        st.info("No new data to upload. All records already exist.")
            else:
                st.error("The processed data resulted in an empty set.")

    except Exception as e:
        st.error(f"Processing Error: {e}")
