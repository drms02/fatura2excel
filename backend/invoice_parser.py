import re
import pdfplumber
from typing import Dict, List, Optional
from io import BytesIO

def extract_invoice_data(pdf_file: BytesIO, filename: str) -> Dict[str, str]:
    """
    Extract invoice data from Turkish GİB E-Arşiv PDF.
    Returns a dictionary with all extracted fields.
    """
    result = {
        "Dosya Adı": filename,
        "Fatura Tarihi": "Okunamadı",
        "Fatura No": "Okunamadı",
        "VKN/TCKN": "Okunamadı",
        "Müşteri Adı": "Okunamadı",
        "Matrah": "Okunamadı",
        "KDV": "Okunamadı",
        "Toplam": "Okunamadı"
    }

    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            full_text = full_text.replace('\n', ' ').replace('  ', ' ')

            result["Fatura Tarihi"] = extract_date(full_text)
            result["Fatura No"] = extract_invoice_number(full_text)
            result["VKN/TCKN"] = extract_tax_id(full_text)
            result["Müşteri Adı"] = extract_customer_name(full_text)
            result["Matrah"] = extract_subtotal(full_text)
            result["KDV"] = extract_tax(full_text)
            result["Toplam"] = extract_total(full_text)

    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")

    return result


def extract_date(text: str) -> str:
    """Extract invoice date (Fatura Tarihi)"""
    patterns = [
        r'Fatura\s*Tarihi[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})',
        r'Tarih[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})',
        r'(?:Düzenlenme|Düzenleme)\s*Tarihi[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    general_date = re.search(r'(\d{2}[-/\.]\d{2}[-/\.]\d{4})', text)
    if general_date:
        return general_date.group(1)

    return "Okunamadı"


def extract_invoice_number(text: str) -> str:
    """Extract invoice number (Fatura No) - 3 letters + 13 digits"""
    patterns = [
        r'Fatura\s*(?:No|Numarası)[\s:]*([A-Z]{3}\d{13})',
        r'(?:Ettn|ETTN)[\s:]*([A-Z0-9-]{36})',
        r'([A-Z]{3}\d{13})',
        r'Seri\s*(?:No|:)\s*([A-Z]{3}).*?(\d{8,13})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return match.group(1) + match.group(2)
            return match.group(1)

    return "Okunamadı"


def extract_tax_id(text: str) -> str:
    """Extract tax ID (VKN/TCKN) - 10 or 11 digits"""
    patterns = [
        r'(?:Vergi|VKN)[\s:]*(?:Kimlik|No|Numarası)?[\s:]*(\d{10})',
        r'(?:TC|TCKN)[\s:]*(?:Kimlik|No|Numarası)?[\s:]*(\d{11})',
        r'V\.K\.N\.?[\s:]*(\d{10})',
        r'T\.C\.?[\s:]*(?:Kimlik)?[\s:]*No[\s:]*(\d{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    standalone_match = re.search(r'\b(\d{10,11})\b', text)
    if standalone_match:
        return standalone_match.group(1)

    return "Okunamadı"


def extract_customer_name(text: str) -> str:
    """Extract customer name (Müşteri Adı/Ünvanı)"""
    patterns = [
        r'Sayın[\s:]*([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]{3,100}?)(?:\s+(?:Vergi|VKN|Adres|Address))',
        r'(?:Müşteri|ALICI)[\s:]*(?:Adı|Ünvanı)?[\s:]*([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s\.&-]{3,100}?)(?:\s+(?:Vergi|VKN|Adres))',
        r'To[\s:]*([A-Za-zÇĞİÖŞÜçğıöşü\s\.&-]{3,100}?)(?:\s+(?:Tax|Address|VAT))'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'\s+', ' ', name)
            return name

    return "Okunamadı"


def extract_subtotal(text: str) -> str:
    """Extract subtotal amount (Matrah/Mal Hizmet Toplam Tutarı)"""
    patterns = [
        r'(?:Mal\s*Hizmet\s*Toplam|Matrah)[\s:]*(?:Tutarı)?[\s:]*(?:TL)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:Toplam|Ara\s*Toplam)[\s:]*(?:Tutar)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})[\s]*(?:TL)?[\s]*(?=.*KDV)',
        r'Matrah[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def extract_tax(text: str) -> str:
    """Extract tax amount (Hesaplanan KDV)"""
    patterns = [
        r'(?:Hesaplanan|Toplam)?\s*KDV[\s:]*(?:Tutarı)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:KDV|VAT)[\s:]*(?:\d+%)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:KDV|Vergi)\s*Tutarı[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def extract_total(text: str) -> str:
    """Extract total amount (Ödenecek Tutar)"""
    patterns = [
        r'(?:Ödenecek|Vergiler\s*Dahil)[\s:]*(?:Toplam)?[\s:]*(?:Tutar)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:Genel|Büyük)\s*Toplam[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:Grand|Total)\s*(?:Total)?[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})[\s]*TL'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def format_amount(amount: str) -> str:
    """Format amount to standard decimal format"""
    amount = amount.replace('.', '').replace(',', '.')

    try:
        float_amount = float(amount)
        return f"{float_amount:.2f}"
    except:
        return amount


def process_multiple_pdfs(files: List[tuple]) -> List[Dict[str, str]]:
    """
    Process multiple PDF files and return list of extracted data.
    files: List of tuples (filename, file_content_bytes)
    """
    results = []

    for filename, file_content in files:
        pdf_bytes = BytesIO(file_content)
        invoice_data = extract_invoice_data(pdf_bytes, filename)
        results.append(invoice_data)

    return results
