# pipeline.py
import os, sys, csv, pickle, time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

import quick_scan
from cc_detector import detect_credit_cards
import text_extractor as tx

# --- Config ---
WHITELIST = {
    ".pdf",".docx",".pptx",".html",".htm",
    ".xlsx",".xls",".csv",".txt",".log",".ini",".cfg",
    ".bak",".tmp",".epub",".odt",".msg",
    ".png",".jpg",".jpeg",".zip",".jar"
}
MAX_SIZE = 100 * 1024 * 1024  # 100 MB
CHECKPOINT = "checkpoint.pkl"
REPORT     = "scan_report.csv"
WORKERS    = os.cpu_count()

# --- Build file list once ---
def gather_files(root):
    files=[]
    for r,_,fs in os.walk(root):
        for f in fs:
            ext = os.path.splitext(f)[1].lower()
            path = os.path.join(r,f)
            if ext in WHITELIST and os.path.getsize(path)<=MAX_SIZE:
                files.append(path)
    return files

# --- Worker task ---
def process_file(path):
    # 1) quick binary scan
    if not quick_scan.quick_cc_scan(path):
        return []
    ext = os.path.splitext(path)[1].lower()
    extractor = tx.EXTRACTORS.get(ext)
    hits=[]
    if extractor:
        for label, text in extractor(path):
            # 4) chunked text scanning (sliding 50 KB windows)
            length=len(text)
            step=50_000
            for i in range(0,length,step):
                chunk=text[i:i+step]
                for r in detect_credit_cards(chunk):
                    # adjust absolute offsets
                    start, end = i+r.start, i+r.end
                    hit= (path, label, start, end, chunk[r.start:r.end].strip())
                    hits.append(hit)
    return hits

# --- Checkpoint management ---
def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        return pickle.load(open(CHECKPOINT,"rb"))
    return set()

def save_checkpoint(done):
    pickle.dump(done, open(CHECKPOINT,"wb"))

# --- Main pipeline ---
def main(root):
    all_files = gather_files(root)
    done = load_checkpoint()
    to_process = [f for f in all_files if f not in done]

    # Prepare CSV
    out = open(REPORT,"a", newline="", encoding="utf-8")
    writer = csv.writer(out)
    if os.path.getsize(REPORT)==0:
        writer.writerow(["timestamp","file","label","start","end","match"])

    # Parallel execution with progress bar
    with ProcessPoolExecutor(WORKERS) as exe:
        futures = {exe.submit(process_file,path):path for path in to_process}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Scanning"):
            path = futures[fut]
            try:
                for hit in fut.result():
                    timestamp = datetime.utcnow().isoformat()
                    writer.writerow([timestamp,*hit])
                done.add(path)
                if len(done)%1000==0:
                    save_checkpoint(done)
            except Exception as e:
                print(f"Error {path}: {e}", file=sys.stderr)

    # Final checkpoint
    save_checkpoint(done)
    out.close()
    print("Done. Report →", REPORT)

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Usage: python pipeline.py <scan_root>")
        sys.exit(1)
    main(sys.argv[1])
