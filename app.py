import streamlit as st
import pandas as pd
from pymongo import MongoClient

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Outward Freight Data", 
    page_icon="🚢", 
    layout="wide"  # Changed to wide for a dashboard feel
)

# --- PROFESSIONAL STYLING (CSS) ---
st.markdown("""
    <style>
    /* Dark Theme Setup */
    .stApp { background-color: #0b0e14; }
    
    /* Typography */
    h1 { color: #00e5ff !important; font-weight: 800 !important; }
    h3 { color: #818cf8 !important; }
    
    /* Custom Glow Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #00e5ff, #2979ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
        transition: 0.3s !important;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.5) !important;
    }
    
    /* File Uploader Border */
    .stFileUploader {
        border: 1px solid #1e293b !important;
        background-color: #0f172a !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MONGODB CONNECTION ---
MONGO_URI = st.secrets["MONGO_URI"]

@st.cache_resource
def get_db_connection():
    return MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)['OWDATA_RJT_DIV']

db = get_db_connection()
collection = db['owdata_csv_file']

# --- APP LAYOUT ---
# Header Section
st.title("Outward Freight Data - Rajkot Division")
st.markdown("### Upload File Here to Clean It's Data & Save in Database...")

# Upload Area
uploaded_file = st.file_uploader("Drop your CSV file here", type="csv")

if uploaded_file is not None:
    try:
        # Processing
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        df = df.dropna(how='all')
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        df = df[df['DVSN'].notna()].drop_duplicates()

        # Metrics & Data Section
        col1, col2 = st.columns([1, 4])
        col1.metric("Rows Ready", len(df), delta="Cleaned")
        
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("🚀 Sync to Database"):
            with st.spinner('Establishing secure connection...'):
                rr_numbers = df['RR NUMBER'].tolist()
                existing = [doc['RR NUMBER'] for doc in collection.find({"RR NUMBER": {"$in": rr_numbers}}, {"RR NUMBER": 1})]
                new_data = df[~df['RR NUMBER'].isin(existing)]
                
                if not new_data.empty:
                    collection.insert_many(new_data.to_dict("records"))
                    st.success(f"Success! {len(new_data)} records synchronized.")
                else:
                    st.warning("No new records found. Data is already up to date.")

    except Exception as e:
        st.error(f"System Error: {e}")
