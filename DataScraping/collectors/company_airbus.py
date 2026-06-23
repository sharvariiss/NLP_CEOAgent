"""
Company Sources collector — official Airbus-owned pages.
  1. ZEROe / hydrogen program page          (1 snapshot doc)
  2. Investors / financial results page     (1 snapshot doc)
  3. Newsroom press releases listing        (1 doc per individual release)
"""
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .base import make_document

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-CEO-Strategic-Intelligence-Agent/1.0; "
                  "academic project; contact: you@example.com)"
}

PAGES = [
    {
        "url": "https://www.airbus.com/en/innovation/energy-transition/hydrogen/zeroe-our-hydrogen-powered-aircraft",
        "title": "ZEROe: Airbus hydrogen-powered aircraft",
    },
    {
        "url": "https://www.airbus.com/en/investors/financial-results",
        "title": "Airbus Investors - Financial Results",
    },
]

PRESS_RELEASES_URL = "https://www.airbus.com/en/newsroom/press-releases"
MAX_PRESS_RELEASES = 18
REQUEST_DELAY = 0.5  # seconds between article fetches — be polite to airbus.com


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    main = soup.find("main") or soup
    chunks = [el.get_text(" ", strip=True) for el in main.find_all(["p", "li", "h1", "h2", "h3"])]
    return "\n".join(c for c in chunks if c)


def _extract_date(soup: BeautifulSoup):
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)
    return None


def _collect_single_pages():
    docs = []
    for page in PAGES:
        try:
            resp = requests.get(page["url"], headers=HEADERS, timeout=20)
            resp.raise_for_status()
            text = _extract_text(resp.text)

            if len(text) < 200:
                print(f"  [warn] {page['url']} returned very little text ({len(text)} chars). "
                      f"Airbus.com is partly React/Next.js-rendered — if this keeps happening, "
                      f"swap requests+bs4 for Playwright/Selenium on this page only.")

            docs.append(make_document(
                source_name="Airbus.com",
                source_category="company",
                title=page["title"],
                url=page["url"],
                published_date=None,
                content=text,
                metadata={"collection_method": "requests+bs4"},
            ))
        except Exception as e:
            print(f"  [error] failed to fetch {page['url']}: {e}")
    return docs


def _extract_press_release_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/newsroom/press-releases/" in href and href.rstrip("/") != PRESS_RELEASES_URL.rstrip("/"):
            links.add(urljoin(base_url, href))
    return sorted(links)


def _collect_press_releases(max_releases=MAX_PRESS_RELEASES):
    docs = []
    try:
        resp = requests.get(PRESS_RELEASES_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [error] failed to fetch press releases listing: {e}")
        return docs

    links = _extract_press_release_links(resp.text, PRESS_RELEASES_URL)
    if not links:
        print("  [warn] found 0 press release links on the listing page. Either "
              "airbus.com changed its markup, or that section loads via client-side "
              "JS. Open the page in a browser, view source, and check whether "
              "'/newsroom/press-releases/' links are present in the raw HTML before "
              "assuming this is broken — if they're not, you'll need Playwright here.")
        return docs

    print(f"  found {len(links)} press release links — fetching up to {max_releases}")
    for url in links[:max_releases]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else url.rstrip("/").rsplit("/", 1)[-1]
            text = _extract_text(resp.text)
            if len(text) < 100:
                continue
            docs.append(make_document(
                source_name="Airbus.com (Press Release)",
                source_category="company",
                title=title,
                url=url,
                published_date=_extract_date(soup),
                content=text,
                metadata={"collection_method": "requests+bs4"},
            ))
        except Exception as e:
            print(f"  [warn] failed to fetch press release {url}: {e}")
        time.sleep(REQUEST_DELAY)

    return docs


def collect():
    docs = _collect_single_pages()
    docs += _collect_press_releases()
    return docs