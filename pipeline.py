# pipeline.py
import os, sys, csv, pickle, time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

import quick_scan
from cc_detector import detect_credit_cards
import config

# --- Config ---
WHITELIST = set(config.EXTRACTORS.keys())
MAX_SIZE = 100 * 1024 * 1024  # 100 MB
CHECKPOINT = "checkpoint.pkl"
REPORT     = "scan_report.csv"
WORKERS    = os.cpu_count() or 4

# --- Build file list once ---
def gather_files(root):
    files = []
    for r, _, fnames in os.walk(root):
        for f in fnames:
            path = os.path.join(r, f)
            ext = os.path.splitext(f)[1].lower()
            size = os.path.getsize(path)
            if ext in WHITELIST and size <= MAX_SIZE:
                files.append(path)
    return files

def process_file(path):
    # Strategy 1: quick binary pre-filter
    if not quick_scan.quick_cc_scan(path):
        return []
    ext = os.path.splitext(path)[1].lower()
    extractor = config.EXTRACTORS.get(ext)
    hits = []
    if extractor:
        # chunked / streamed extraction
        for label, text in extractor(path):
            length = len(text)
            step = 50_000
            for i in range(0, length, step):
                chunk = text[i : i + step]
                for r in detect_credit_cards(chunk):
                    start, end = i + r.start, i + r.end
                    snippet = chunk[r.start:r.end].strip().replace("\n", " ")
                    hits.append((path, label, start, end, snippet))
    return hits

def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        return pickle.load(open(CHECKPOINT, "rb"))
    return set()

def save_checkpoint(done):
    pickle.dump(done, open(CHECKPOINT, "wb"))

def main(root):
    all_files = gather_files(root)
    done = load_checkpoint()
    to_process = [f for f in all_files if f not in done]

    # Prepare report
    mode = "a" if os.path.exists(REPORT) else "w"
    rep = open(REPORT, mode, newline="", encoding="utf-8")
    writer = csv.writer(rep)
    if mode == "w":
        writer.writerow(["timestamp","file","label","start","end","match"])

    start = time.perf_counter()
    with ProcessPoolExecutor(WORKERS) as exe:
        futures = {exe.submit(process_file, p): p for p in to_process}
        for fut in tqdm(as_completed(futures),
                        total=len(futures),
                        desc="Scanning"):
            path = futures[fut]
            try:
                for hit in fut.result():
                    timestamp = datetime.utcnow().isoformat()
                    writer.writerow([timestamp, *hit])
                done.add(path)
                if len(done) % 1000 == 0:
                    save_checkpoint(done)
            except Exception as e:
                print(f"Error {path}: {e}", file=sys.stderr)

    save_checkpoint(done)
    rep.close()
    elapsed = time.perf_counter() - start
    print(f"Scan complete in {elapsed:.1f}s. Report: {REPORT}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <scan_root>")
        sys.exit(1)
    main(sys.argv[1])