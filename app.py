import streamlit as st
import pandas as pd
from pymongo import MongoClient

# 1. अपना कनेक्शन लिंक यहाँ डालें (पासवर्ड के साथ)
MONGO_URI = "mongodb+srv://hapacgs_db_user:emCe7cPkxuJlbvvI@cluster0.auqaw1p.mongodb.net"

@st.cache_resource
def get_db_connection():
    # SSL Error को फिक्स करने के लिए tlsAllowInvalidCertificates=True जोड़ा गया है
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client['OWDATA_RJT_DIV']

db = get_db_connection()
collection = db['owdata_csv_file']

st.title("CSV Data Cleaner & Uploader")

uploaded_file = st.file_uploader("अपनी CSV फाइल यहाँ अपलोड करें", type="csv")

if uploaded_file is not None:
    try:
        # फाइल पढ़ना
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        
        # --- CLEANING RULES ---
        df = df.dropna(how='all')
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        df = df[df['DVSN'].notna()]
        df = df.drop_duplicates()
        # ----------------------

        st.write(f"### कुल क्लीन की गई पंक्तियाँ: {len(df)}")
        st.dataframe(df.head(5)) 

        # डेटाबेस में सेव करना (डुप्लीकेट चेक के साथ)
        if st.button("डेटाबेस में सेव करें"):
            if not df.empty:
                # RR NUMBER के आधार पर डुप्लीकेट चेक करें
                rr_numbers = df['RR NUMBER'].tolist()
                # चेक करें कि क्या ये RR NUMBERS पहले से डेटाबेस में हैं
                existing_docs = collection.find({"RR NUMBER": {"$in": rr_numbers}}, {"RR NUMBER": 1})
                existing_rrs = [doc['RR NUMBER'] for doc in existing_docs]
                
                # नया डेटा फिल्टर करें
                new_data = df[~df['RR NUMBER'].isin(existing_rrs)]
                
                if not new_data.empty:
                    collection.insert_many(new_data.to_dict("records"))
                    st.success(f"सफलतापूर्वक {len(new_data)} नई पंक्तियाँ सेव की गईं!")
                    if len(df) > len(new_data):
                        st.warning(f"{len(df) - len(new_data)} पंक्तियाँ पहले से मौजूद थीं (Duplicate)।")
                else:
                    st.info("इस फाइल का सारा डेटा पहले से डेटाबेस में मौजूद है।")
            else:
                st.error("डेटा खाली है!")

    except Exception as e:
        st.error(f"Error processing file: {e}")
