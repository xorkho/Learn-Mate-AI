import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """
    Given a PDF file path, extract all text from it.
    """
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_txt(file_path: str) -> str:
    """
    Given a .txt file path, read and return its content.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(file_path: str, extension: str) -> str:
    """
    Dispatch to the right extraction method based on file extension.
    """
    if extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif extension == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")