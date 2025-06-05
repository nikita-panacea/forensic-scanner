import streamlit as st
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

st.title("Credit Card Scan Results")

res = es.search(index="docs", body={
    "query": {
        "exists": {
            "field": "cc_matches"
        }
    },
    "size": 1000
})

for hit in res["hits"]["hits"]:
    src = hit["_source"]
    st.markdown(f"**{src['filename']} - Page {src['page']}**")
    st.code(f"Matches: {src['cc_matches']}")
    with st.expander("View Text"):
        st.text(src["text"])
