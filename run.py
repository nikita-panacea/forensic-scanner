# import os
# from text_extractor import extract_text_from_pdf, extract_text_from_docx
# from cc_detector import detect_credit_cards

# def scan_folder(folder):
#     print('the folder is #####   ',folder)
#     #create_index()
#     for root, _, files in os.walk(folder):
#         print('file', files)
#         for file in files:
#             path = os.path.join(root, file)
#             if file.endswith(".pdf"):
#                 pages = extract_text_from_pdf(path)
#             elif file.endswith(".docx"):
#                 pages = extract_text_from_docx(path)
#             else:
#                 continue
#             print('pages', pages)
#             for page_num, text in pages:
#                 if not text:
#                     print('no text found')
#                     continue
#                 findings = detect_credit_cards(text)
#                 matches = [text[f.start:f.end] for f in findings]
#                 if matches:
#                     print(f"[!] CC found in {file} Page {page_num}: {matches}")
#                 # index_page(file, path, page_num, text, matches)

# if __name__ == "__main__":
#     folder = input("Enter folder path to scan: ")
#     scan_folder(folder)

import os, sys, csv, time
from datetime import datetime, timedelta
from cc_detector import detect_credit_cards
import text_extractor as tx

# Supported extensions (including logs etc.)
TEXT_EXTS = {".txt",".log",".ini",".cfg",".bak",".tmp"}
EXTRACTORS = {
    ".pdf": tx.extract_text_from_pdf,
    ".docx": tx.extract_text_from_docx,
    ".pptx": tx.extract_text_from_pptx,
    ".html": tx.extract_text_from_html,
    ".htm": tx.extract_text_from_html,
    ".xlsx": tx.extract_text_from_xlsx,
    ".xls": tx.extract_text_from_xlsx,
    ".csv": tx.extract_text_from_csv,
    **{ext: tx.extract_text_from_txt for ext in TEXT_EXTS},
    ".epub": tx.extract_text_from_epub,
    ".odt": tx.extract_text_from_odt,
    ".msg": tx.extract_text_from_msg,
    ".png": tx.extract_text_from_image,
    ".jpg": tx.extract_text_from_image,
    ".jpeg": tx.extract_text_from_image,
    ".zip": tx.extract_text_from_zip,
    ".jar": tx.extract_text_from_zip,
}

def scan_folder(folder, report_path="scan_report.csv"):
    # Gather all files first
    files = []
    for root, _, fnames in os.walk(folder):
        for name in fnames:
            if os.path.splitext(name)[1].lower() in EXTRACTORS:
                files.append(os.path.join(root, name))
    total = len(files)
    if total == 0:
        print("No supported files found.")
        return

    # Prepare CSV
    with open(report_path, "w", newline="", encoding="utf-8") as rep:
        writer = csv.writer(rep)
        writer.writerow([
            "timestamp", "file", "label", "start", "end", "match"
        ])

        start_time = time.perf_counter()
        for idx, path in enumerate(files, 1):
            now = datetime.now().isoformat(timespec="seconds")
            elapsed = time.perf_counter() - start_time
            avg = elapsed / idx
            remaining = avg * (total - idx)
            eta = (datetime.now() + timedelta(seconds=remaining)).isoformat(timespec="seconds")
            print(f"[{now}] Processing ({idx}/{total}) {path}")
            print(f"    Elapsed: {elapsed:.1f}s  ETA: {eta}")

            ext = os.path.splitext(path)[1].lower()
            extractor = EXTRACTORS.get(ext)
            try:
                for label, text in extractor(path):
                    if not text or not text.strip():
                        continue
                    results = detect_credit_cards(text)
                    for r in results:
                        match = text[r.start:r.end].replace("\n"," ")
                        writer.writerow([now, path, label, r.start, r.end, match])
            except Exception as e:
                print(f"  [ERROR] {path}: {e}")

    print(f"\nScan complete. Report saved to {report_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run.py <folder_to_scan>")
        sys.exit(1)
    scan_folder(sys.argv[1])
