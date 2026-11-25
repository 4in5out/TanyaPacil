import logging
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract readable text page-by-page from a PDF file."""
    path = Path(file_path)
    if not path.exists():
        return ''

    try:
        reader = PdfReader(str(path))
        pages = []
        for idx, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or '').strip()
            if text:
                pages.append(f"[Page {idx}]\n{text}")
        return '\n\n'.join(pages)
    except Exception as exc:
        logger.warning("Failed to extract PDF text from %s: %s", path, exc)
        return ''


def extract_text_from_url(url: str, timeout: int = 10) -> str:
    """Best-effort text extraction for external resources like GFG or W3Schools."""
    if not url:
        return ''

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TanyaPacilBot/1.0; +https://cs.ui.ac.id)'
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()

        main = soup.find('main') or soup.find('article') or soup.body
        raw_text = main.get_text(separator='\n') if main else soup.get_text(separator='\n')
        cleaned = re.sub(r'\n{3,}', '\n\n', raw_text)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        # Keep up to ~25k chars per external page to avoid bloat
        return '\n'.join(lines)[:25000]
    except Exception as exc:
        logger.warning("Failed to fetch external URL %s: %s", url, exc)
        return ''
