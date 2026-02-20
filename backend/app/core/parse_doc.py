import fitz

def extract_text_from_pdf(file_path: str) -> str:
    """
    纯粹的解析函数。
    它不知道 LangGraph 的存在，只负责把文件变文本。
    """
    if not file_path.endswith('.pdf'):
        raise ValueError("非 PDF 文件")
        
    doc = fitz.open(file_path)
    text = "".join([page.get_text() for page in doc])
    return text