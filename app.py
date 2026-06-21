import streamlit as st
import pandas as pd
from pymongo import MongoClient

# यह लाइन st.secrets["MONGO_URI"] का उपयोग करती है, जो आपने Cloud Settings में डाला है
MONGO_URI = st.secrets["MONGO_URI"]

@st.cache_resource
def get_db_connection():
    # SSL Handshake एरर को रोकने के लिए tlsAllowInvalidCertificates=True जरूरी है
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
    return client['OWDATA_RJT_DIV']

db = get_db_connection()
collection = db['owdata_csv_file']

st.title("CSV Data Cleaner & Uploader")

uploaded_file = st.file_uploader("अपनी CSV फाइल यहाँ अपलोड करें", type="csv")

if uploaded_file is not None:
    try:
        # फाइल प्रोसेस करना
        df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='latin1', header=2)
        
        # --- क्लीनिंग लॉजिक ---
        df = df.dropna(how='all')
        df = df[~df.astype(str).apply(lambda x: x.str.contains('TOTAL|GRAND TOTAL', case=False, na=False)).any(axis=1)]
        df = df[df['DVSN'].notna()]
        df = df.drop_duplicates()
        # ----------------------

        st.write(f"### कुल क्लीन की गई पंक्तियाँ: {len(df)}")
        st.dataframe(df.head(5))

        if st.button("डेटाबेस में सेव करें"):
            if not df.empty:
                # डुप्लीकेट चेक (RR NUMBER के आधार पर)
                rr_numbers = df['RR NUMBER'].tolist()
                existing_docs = collection.find({"RR NUMBER": {"$in": rr_numbers}}, {"RR NUMBER": 1})
                existing_rrs = [doc['RR NUMBER'] for doc in existing_docs]
                
                new_data = df[~df['RR NUMBER'].isin(existing_rrs)]
                
                if not new_data.empty:
                    collection.insert_many(new_data.to_dict("records"))
                    st.success(f"सफलतापूर्वक {len(new_data)} नई पंक्तियाँ सेव की गईं!")
                else:
                    st.info("डेटा पहले से ही मौजूद है।")
            else:
                st.error("डेटा खाली है!")

    except Exception as e:
        st.error(f"Error processing file: {e}")
