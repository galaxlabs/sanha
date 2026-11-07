"""Read bounded DOCX content in memory; never execute Office or external links."""
import io
import re
import zipfile
from xml.etree import ElementTree

WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff")


def read_word(content):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        if len(entries) > 5000 or sum(item.file_size for item in entries) > 64 * 1024 * 1024:
            raise ValueError("Word archive exceeds review expansion limits")
        names = {item.filename: item for item in entries}
        if "word/document.xml" not in names:
            raise ValueError("Not a DOCX Word document")
        paragraphs = []
        parts = ["word/document.xml"] + sorted(name for name in names if re.fullmatch(r"word/(?:header|footer)\d+\.xml", name))
        for name in parts:
            if names[name].file_size > 4 * 1024 * 1024:
                raise ValueError("Word XML part too large")
            xml = archive.read(name)
            if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                raise ValueError("Document entity declarations not supported")
            root = ElementTree.fromstring(xml)
            for paragraph in root.iter(WORD + "p"):
                text = "".join(element.text or "" for element in paragraph.iter(WORD + "t")).strip()
                if text:
                    paragraphs.append(text)
        text = "\n".join(paragraphs)
        pages = [(index // 6000 + 1, text[index:index + 6000]) for index in range(0, min(len(text), 120000), 6000)]
        media = sorted(name for name in names if name.startswith("word/media/") and name.lower().endswith(IMAGES))
        images = []
        for name in media[:20]:
            if names[name].file_size <= 16 * 1024 * 1024:
                images.append((name, archive.read(name)))
        return {"pages": pages, "images": images, "truncated": len(text) > 120000 or len(media) > 20}
