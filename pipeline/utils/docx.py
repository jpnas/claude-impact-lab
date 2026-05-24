import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def read_docx_text(path: Path) -> str:
    """Extract plain text from a DOCX file without python-docx."""
    with zipfile.ZipFile(path) as zf:
        try:
            with zf.open("word/document.xml") as f:
                tree = ET.parse(f)
        except KeyError:
            raise ValueError(f"Not a valid DOCX (missing word/document.xml): {path}")
    root = tree.getroot()
    paras = []
    for p in root.iter(f"{{{_W}}}p"):
        texts = [t.text or "" for t in p.iter(f"{{{_W}}}t")]
        paras.append("".join(texts))
    return "\n".join(paras)
