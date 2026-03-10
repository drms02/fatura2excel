import xml.etree.ElementTree as ET
from typing import Dict

# GİB UBL-TR namespace map
NS = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
}


def _get(root, xpath: str) -> str:
    el = root.find(xpath, NS)
    if el is not None and el.text:
        return el.text.strip()
    return "Okunamadı"


def extract_xml_invoice(xml_content: bytes, filename: str) -> Dict[str, str]:
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
        root = ET.fromstring(xml_content)

        # Fatura No
        result["Fatura No"] = _get(root, 'cbc:ID')

        # Fatura Tarihi: YYYY-MM-DD → DD.MM.YYYY
        date_raw = _get(root, 'cbc:IssueDate')
        if date_raw != "Okunamadı":
            parts = date_raw.split('-')
            if len(parts) == 3:
                result["Fatura Tarihi"] = f"{parts[2]}.{parts[1]}.{parts[0]}"
            else:
                result["Fatura Tarihi"] = date_raw

        # Fatura Tipi
        inv_type = _get(root, 'cbc:InvoiceTypeCode')
        if inv_type != "Okunamadı":
            mapping = {"SATIS": "SATIŞ", "IADE": "İADE", "TEVKIFAT": "TEVKİFAT"}
            result["Fatura Tipi"] = mapping.get(inv_type.upper(), inv_type.upper())

        # Para Birimi
        currency = _get(root, 'cbc:DocumentCurrencyCode')
        if currency != "Okunamadı":
            result["Para Birimi"] = {"TRY": "TL"}.get(currency, currency)

        # Satıcı
        result["Satıcı Adı"] = _get(
            root, 'cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name'
        )
        result["Satıcı VKN"] = _get(
            root, 'cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID'
        )

        # Alıcı
        result["Alıcı Adı"] = _get(
            root, 'cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name'
        )
        buyer_id = _get(
            root, 'cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID'
        )
        if buyer_id == "Okunamadı":
            buyer_id = _get(
                root, 'cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID'
            )
        result["Alıcı VKN/TCKN"] = buyer_id

        # KDV alanları
        tax_total = root.find('cac:TaxTotal', NS)
        if tax_total is not None:
            kdv_el = tax_total.find('cbc:TaxAmount', NS)
            if kdv_el is not None and kdv_el.text:
                result["KDV"] = f"{float(kdv_el.text.strip()):.2f}"

            subtotals = tax_total.findall('cac:TaxSubtotal', NS)
            rates = []
            matrah_total = 0.0
            for sub in subtotals:
                pct = sub.find('cac:TaxCategory/cbc:Percent', NS)
                if pct is not None and pct.text:
                    rate = f"%{int(float(pct.text.strip()))}"
                    if rate not in rates:
                        rates.append(rate)
                taxable = sub.find('cbc:TaxableAmount', NS)
                if taxable is not None and taxable.text:
                    try:
                        matrah_total += float(taxable.text.strip())
                    except Exception:
                        pass
            if rates:
                result["KDV Oranı"] = ", ".join(rates)
            if matrah_total > 0:
                result["Matrah"] = f"{matrah_total:.2f}"

        # Toplam
        payable = _get(root, 'cac:LegalMonetaryTotal/cbc:PayableAmount')
        if payable != "Okunamadı":
            result["Toplam"] = f"{float(payable):.2f}"

    except Exception as e:
        print(f"XML parse error {filename}: {e}")

    return result
