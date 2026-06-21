import streamlit as st
import pandas as pd
from pymongo import MongoClient

# Page Configuration
st.set_page_config(page_title="CSV Data Uploader", page_icon="📊", layout="centered")

# MongoDB Connection
MONGO_URI = st.secrets["MONGO_URI"]

@st.cache_resource
def get_db_connection():
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client['OWDATA_RJT_DIV']

db = get_db_connection()
collection = db['owdata_csv_file']

# UI - Title and Description
st.title("📊 Upload Outward Freight Data CSV File Here ...")
st.markdown("Downloaded from FOIS Webportal Data to be paste here for cleaning and saving in MongoDB Database")

# File Uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # File Processing
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        
        # --- Cleaning Logic ---
        df = df.dropna(how='all')
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        df = df[df['DVSN'].notna()]
        df = df.drop_duplicates()
        # ----------------------

        st.subheader("Data Preview")
        st.write(f"Cleaned rows: **{len(df)}**")
        st.dataframe(df.head(10), use_container_width=True)

        if st.button("Save to Database"):
            if not df.empty:
                with st.spinner('Checking for duplicates and saving...'):
                    # Duplicate check based on RR NUMBER
                    rr_numbers = df['RR NUMBER'].tolist()
                    existing_docs = collection.find({"RR NUMBER": {"$in": rr_numbers}}, {"RR NUMBER": 1})
                    existing_rrs = [doc['RR NUMBER'] for doc in existing_docs]
                    
                    new_data = df[~df['RR NUMBER'].isin(existing_rrs)]
                    
                    if not new_data.empty:
                        collection.insert_many(new_data.to_dict("records"))
                        st.success(f"Successfully saved {len(new_data)} new records!")
                        
                        if len(df) > len(new_data):
                            st.warning(f"{len(df) - len(new_data)} records were duplicates and skipped.")
                    else:
                        st.info("All records in this file already exist in the database.")
            else:
                st.error("The processed data is empty!")

    except Exception as e:
        st.error(f"Error processing file: {e}")
