import json
import os
from pathlib import Path
from typing import Optional

import fitz
import pytesseract
from docx import Document
from pdf2image import convert_from_path

from .config import settings

OCR_CONFIG = '--psm 1'


def extract_pdf_text(path: Path) -> str:
    document = fitz.open(path)
    text_chunks = []
    for page in document:
        page_text = page.get_text().strip()
        if page_text:
            text_chunks.append(page_text)
    full_text = '\n'.join(text_chunks).strip()
    if len(full_text) < 100:
        return extract_pdf_text_ocr(path)
    return full_text


def extract_pdf_text_ocr(path: Path) -> str:
    pages = convert_from_path(str(path), dpi=300)
    text_pages = []
    for page in pages:
        text_pages.append(pytesseract.image_to_string(page, config=OCR_CONFIG))
    return '\n'.join(text_pages).strip()


def extract_docx_text(path: Path) -> str:
    document = Document(path)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs).strip()


def extract_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        return extract_pdf_text(path)
    if suffix in ['.docx', '.doc']:
        return extract_docx_text(path)
    raise ValueError('Unsupported document type: ' + suffix)


def save_uploaded_file(uploaded_file, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('wb') as buffer:
        buffer.write(uploaded_file.file.read())
    return destination
