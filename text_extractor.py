import pdfplumber
from docx import Document

def extract_text_from_pdf(file_path):
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            texts.append((i + 1, page.extract_text()))
    return texts

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    return [(1, full_text)]
