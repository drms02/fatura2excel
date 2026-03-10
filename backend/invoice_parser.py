import re
import pdfplumber
from typing import Dict, List
from io import BytesIO


def extract_invoice_data(pdf_file: BytesIO, filename: str) -> Dict[str, str]:
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
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

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
    patterns = [
        r'Fatura\s*Tarihi[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})',
        r'(?:Düzenlenme|Düzenleme)\s*Tarihi[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})',
        r'Tarih[\s:]*(\d{2}[-/\.]\d{2}[-/\.]\d{4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    # fallback: ilk tarihi al
    match = re.search(r'(\d{2}[-/\.]\d{2}[-/\.]\d{4})', text)
    if match:
        return match.group(1)

    return "Okunamadı"


def extract_invoice_number(text: str) -> str:
    patterns = [
        # SA42026000275539 gibi: 2-3 harf + 1-2 rakam + 13 rakam toplam 16 karakter
        r'Fatura\s*No[\s:]*([A-Z]{2,3}\d{14,15})',
        # Standart: 3 harf + 13 rakam
        r'Fatura\s*No[\s:]*([A-Z]{3}\d{13})',
        # Genel alfanumerik prefix
        r'Fatura\s*No[\s:]*([A-Z0-9]{3,5}\d{10,15})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return "Okunamadı"


def extract_tax_id(text: str) -> str:
    # Önce müşteri TCKN'sini dene (11 hane, "Kimlik Numarası" yakınında)
    patterns = [
        r'Kimlik\s*Numaras[ıi][\s:]*(\d{11})',
        r'(?:TC|TCKN)[\s:]*(?:Kimlik|No|Numaras[ıi])?[\s:]*(\d{11})',
        r'T\.C\.?\s*(?:Kimlik)?\s*No[\s:]*(\d{11})',
        # VKN (10 hane) - müşteri vergi no
        r'(?:Alıcı|Müşteri)[^\n]*?Vergi[^\n]*?(\d{10})',
        r'V\.K\.N\.?[\s:]*(\d{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: herhangi 10-11 haneli sayı
    match = re.search(r'\b(\d{10,11})\b', text)
    if match:
        return match.group(1)

    return "Okunamadı"


def extract_customer_name(text: str) -> str:
    patterns = [
        # "Sayın" ile başlayan
        r'Say[ıi]n[\s:]*([A-ZÇĞİÖŞÜ][^\n]{3,80}?)(?:\s+(?:Fatura|Vergi|VKN|Adres|E-Posta|Tel))',
        # İsim satırı + "Fatura No:" aynı satırda
        r'^([A-ZÇĞİÖŞÜ][a-zA-ZÇĞİÖŞÜçğıöşü\s\.]{5,60}?)\s+Fatura\s+No\s*:',
        # "Müşteri" veya "ALICI" etiketi
        r'(?:Müşteri|ALICI)\s*(?:Adı|Ünvanı)?[\s:]*([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü\s\.&\-]{3,80}?)(?:\s+(?:Vergi|VKN|Adres))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 2:
                return name

    return "Okunamadı"


def extract_subtotal(text: str) -> str:
    patterns = [
        # "Mal / Hizmet Toplam Tutarı:" veya "Mal Hizmet Toplam Tutarı:"
        r'Mal\s*/?\s*Hizmet\s*Toplam\s*Tutar[ıi][\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Matrah[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def extract_tax(text: str) -> str:
    patterns = [
        # "Hesaplanan KDV(%20):" — parantez içini atla
        r'Hesaplanan\s*KDV\s*(?:\([^)]*\))?\s*[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Toplam\s*KDV\s*(?:\([^)]*\))?\s*[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'KDV\s*Tutar[ıi][\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def extract_total(text: str) -> str:
    patterns = [
        r'[Öö]denecek\s*Tutar[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Vergiler\s*Dahil\s*Toplam\s*Tutar[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'(?:Genel|Büyük)\s*Toplam[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))

    return "Okunamadı"


def format_amount(amount: str) -> str:
    """Türkçe format: 1.999,17 → 1999.17"""
    amount = amount.strip()
    # Türkçe: nokta=binlik, virgül=ondalık
    amount = amount.replace('.', '').replace(',', '.')
    try:
        return f"{float(amount):.2f}"
    except Exception:
        return amount


def process_multiple_pdfs(files: List[tuple]) -> List[Dict[str, str]]:
    results = []
    for filename, file_content in files:
        pdf_bytes = BytesIO(file_content)
        invoice_data = extract_invoice_data(pdf_bytes, filename)
        results.append(invoice_data)
    return results
