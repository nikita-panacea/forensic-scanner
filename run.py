import os
from text_extractor import extract_text_from_pdf, extract_text_from_docx
from cc_detector import detect_credit_cards
from indexer import create_index, index_page

def scan_folder(folder):
    create_index()
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            if file.endswith(".pdf"):
                pages = extract_text_from_pdf(path)
            elif file.endswith(".docx"):
                pages = extract_text_from_docx(path)
            else:
                continue

            for page_num, text in pages:
                if not text:
                    continue
                findings = detect_credit_cards(text)
                matches = [text[f.start:f.end] for f in findings]
                if matches:
                    print(f"[!] CC found in {file} Page {page_num}: {matches}")
                index_page(file, path, page_num, text, matches)

if __name__ == "__main__":
    folder = input("Enter folder path to scan: ")
    scan_folder(folder)
