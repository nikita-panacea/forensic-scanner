from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

def create_index():
    if not es.indices.exists(index="docs"):
        es.indices.create(index="docs")

def index_page(filename, path, page_num, text, cc_hits):
    doc_id = f"{filename}_{page_num}"
    es.index(index="docs", id=doc_id, body={
        "filename": filename,
        "path": path,
        "page": page_num,
        "text": text,
        "cc_matches": cc_hits
    })
