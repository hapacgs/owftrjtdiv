import streamlit as st
import pandas as pd
from pymongo import MongoClient

# 1. अपना कनेक्शन लिंक यहाँ डालें (पासवर्ड के साथ)
MONGO_URI = "mongodb+srv://hapacgs_db_user:emCe7cPkxuJlbvvI@cluster0.auqaw1p.mongodb.net"

@st.cache_resource
def get_db_connection():
    try:
        client = MongoClient(MONGO_URI)
        return client['OWDATA_RJT_DIV']
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

db = get_db_connection()
collection = db['owdata_csv_file']

st.title("CSV Data Cleaner & Uploader")

uploaded_file = st.file_uploader("अपनी CSV फाइल अपलोड करें", type="csv")

if uploaded_file is not None:
    try:
        # फाइल पढ़ना
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        
        # --- CLEANING RULES ---
        # 1. पूरी तरह खाली रो हटाना
        df = df.dropna(how='all')
        
        # 2. 'TOTAL', 'GRAND TOTAL' वाली रो हटाना (सभी कॉलम में चेक करेगा)
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        
        # 3. 'DVSN' कॉलम में None या खाली वैल्यू वाली रो हटाना
        df = df[df['DVSN'].notna()]
        
        # 4. डुप्लीकेट एंट्रीज हटाना
        df = df.drop_duplicates()
        # ----------------------

        st.write(f"### कुल क्लीन की गई पंक्तियाँ: {len(df)}")
        st.dataframe(df.head(10)) # शुरुआती 10 रो दिखाएं

        # डेटाबेस में सेव करना
        if st.button("डेटाबेस में सेव करें"):
            if not df.empty:
                data_dict = df.to_dict("records")
                collection.insert_many(data_dict)
                st.success(f"सफलतापूर्वक {len(df)} पंक्तियाँ सेव हो गईं!")
                st.write("कॉलम के नाम:", list(df.columns))
            else:
                st.error("डेटा खाली है!")

    except Exception as e:
        st.error(f"Error processing file: {e}")