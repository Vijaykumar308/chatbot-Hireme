from pypdf import PdfReader


def extract_text_from_pdf(path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)
