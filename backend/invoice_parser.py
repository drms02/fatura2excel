import re
import pdfplumber
from typing import Dict, List
from io import BytesIO


def extract_invoice_data(pdf_file: BytesIO, filename: str) -> Dict[str, str]:
    result = {
        "Dosya Adı": filename,
        "Fatura Tarihi": "Okunamadı",
        "Fatura No": "Okunamadı",
        "Fatura Tipi": "Okunamadı",
        "Satıcı Adı": "Okunamadı",
        "Satıcı VKN": "Okunamadı",
        "Alıcı Adı": "Okunamadı",
        "Alıcı VKN/TCKN": "Okunamadı",
        "Para Birimi": "TL",
        "Matrah": "Okunamadı",
        "KDV Oranı": "Okunamadı",
        "KDV": "Okunamadı",
        "Toplam": "Okunamadı",
    }

    try:
        with pdfplumber.open(pdf_file) as pdf:
            lines = []
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))
                    full_text += text + "\n"

            result["Fatura Tarihi"] = extract_date(full_text)
            result["Fatura No"] = extract_invoice_number(full_text)
            result["Fatura Tipi"] = extract_invoice_type(full_text)
            result["Satıcı Adı"] = extract_seller_name(lines)
            result["Satıcı VKN"] = extract_seller_vkn(full_text)
            result["Alıcı Adı"] = extract_customer_name(full_text)
            result["Alıcı VKN/TCKN"] = extract_buyer_tax_id(full_text)
            result["Para Birimi"] = extract_currency(full_text)
            result["Matrah"] = extract_subtotal(full_text)
            result["KDV Oranı"] = extract_tax_rate(full_text)
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
    match = re.search(r'(\d{2}[-/\.]\d{2}[-/\.]\d{4})', text)
    if match:
        return match.group(1)
    return "Okunamadı"


def extract_invoice_number(text: str) -> str:
    patterns = [
        r'Fatura\s*No[\s:]*([A-Z]{2,3}\d{14,15})',
        r'Fatura\s*No[\s:]*([A-Z]{3}\d{13})',
        r'Fatura\s*No[\s:]*([A-Z0-9]{3,5}\d{10,15})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Okunamadı"


def extract_invoice_type(text: str) -> str:
    match = re.search(r'Fatura\s*Tipi[\s:]*([A-ZÇĞİÖŞÜa-zçğıöşü]+)', text, re.IGNORECASE)
    if match:
        val = match.group(1).strip().upper()
        # Türkçeleştir
        mapping = {"SATIS": "SATIŞ", "IADE": "İADE", "TEVKIFAT": "TEVKİFAT"}
        return mapping.get(val, val)
    return "Okunamadı"


def extract_seller_name(lines: list) -> str:
    """İlk anlamlı satır satıcı adıdır."""
    skip_keywords = ['tel:', 'faks:', 'web sitesi:', 'vergi', 'mersis', 'ticaret sicil',
                     'senaryo:', 'e-arşiv', 'özelleştirme']
    for line in lines:
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if any(kw in lower for kw in skip_keywords):
            continue
        # Adres satırları genelde rakamla veya posta koduyla başlar
        if re.match(r'^\d{5}', line):
            continue
        if len(line) > 5:
            return line
    return "Okunamadı"


def extract_seller_vkn(text: str) -> str:
    """Satıcıya ait Vergi Numarası (10 hane)"""
    patterns = [
        r'Vergi\s*Numaras[ıi][\s:]*(\d{10})',
        r'V\.K\.N\.?[\s:]*(\d{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Okunamadı"


def extract_buyer_tax_id(text: str) -> str:
    """Alıcıya ait TCKN (11 hane) veya VKN (10 hane)"""
    patterns = [
        r'Kimlik\s*Numaras[ıi][\s:]*(\d{11})',
        r'(?:TC|TCKN)[\s:]*(?:Kimlik|No|Numaras[ıi])?[\s:]*(\d{11})',
        r'T\.C\.?\s*(?:Kimlik)?\s*No[\s:]*(\d{11})',
        r'Alıcı[^\n]*?Vergi[^\n]*?(\d{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Okunamadı"


def extract_customer_name(text: str) -> str:
    patterns = [
        r'Say[ıi]n[\s:]*([A-ZÇĞİÖŞÜ][^\n]{3,80}?)(?:\s+(?:Fatura|Vergi|VKN|Adres|E-Posta|Tel))',
        r'^([A-ZÇĞİÖŞÜ][a-zA-ZÇĞİÖŞÜçğıöşü\s\.]{5,60}?)\s+Fatura\s+No\s*:',
        r'(?:Müşteri|ALICI)\s*(?:Adı|Ünvanı)?[\s:]*([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü\s\.&\-]{3,80}?)(?:\s+(?:Vergi|VKN|Adres))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = re.sub(r'\s+', ' ', match.group(1).strip())
            if len(name) > 2:
                return name
    return "Okunamadı"


def extract_currency(text: str) -> str:
    """Para birimi: TL, USD, EUR, GBP"""
    if re.search(r'\bUSD\b|\$', text):
        return "USD"
    if re.search(r'\bEUR\b|€', text):
        return "EUR"
    if re.search(r'\bGBP\b|£', text):
        return "GBP"
    return "TL"


def extract_subtotal(text: str) -> str:
    patterns = [
        r'Mal\s*/?\s*Hizmet\s*Toplam\s*Tutar[ıi][\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        r'Matrah[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return format_amount(match.group(1))
    return "Okunamadı"


def extract_tax_rate(text: str) -> str:
    """KDV oranı — tek veya çok oranlı faturalarda tümünü yakalar."""
    rates = re.findall(r'Hesaplanan\s*KDV\s*\((%\d+|\d+%)\)', text, re.IGNORECASE)
    if not rates:
        rates = re.findall(r'KDV\s*\((%\d+|\d+%)\)', text, re.IGNORECASE)
    if not rates:
        rates = re.findall(r'KDV\s+(%\d{1,2}|\d{1,2}%)', text, re.IGNORECASE)
    if rates:
        # Normalize: hepsi %XX formatına çek, tekrarları kaldır
        normalized = []
        seen = set()
        for r in rates:
            r = r if r.startswith('%') else '%' + r
            if r not in seen:
                seen.add(r)
                normalized.append(r)
        return ", ".join(normalized)
    return "Okunamadı"


def extract_tax(text: str) -> str:
    """KDV tutarı — çok oranlı faturalarda tüm KDV'leri toplar."""
    # Önce genel toplam KDV satırını ara
    total_match = re.search(
        r'(?:Toplam\s*KDV|KDV\s*Tutar[ıi])[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        text, re.IGNORECASE
    )
    if total_match:
        return format_amount(total_match.group(1))

    # Çok oranlı: tüm "Hesaplanan KDV(...): X,XX" satırlarını topla
    amounts = re.findall(
        r'Hesaplanan\s*KDV\s*(?:\([^)]*\))?\s*[\s:]*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
        text, re.IGNORECASE
    )
    if amounts:
        total = sum(
            float(a.replace('.', '').replace(',', '.')) for a in amounts
        )
        return f"{total:.2f}"

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
    amount = amount.strip().replace('.', '').replace(',', '.')
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
