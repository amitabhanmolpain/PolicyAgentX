import requests, PyPDF2, io

PDF_SOURCES = {
    "economic_survey_2024": "https://indiabudget.gov.in/economicsurvey/doc/echapter.pdf",
    "rbi_handbook":         "https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/0HSIE_F.PDF",
}

def pdf_to_text(url: str) -> str:
    r = requests.get(url, timeout=30)
    reader = PyPDF2.PdfReader(io.BytesIO(r.content))
    return "\n".join(
        page.extract_text() for page in reader.pages if page.extract_text()
    )