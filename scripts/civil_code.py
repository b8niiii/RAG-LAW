"""Convert an official Normattiva Akoma Ntoso export of the Civil Code."""

import argparse
from datetime import date
import gzip
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile


SOURCE = (
    "https://www.normattiva.it/uri-res/N2Ls?"
    "urn:nir:stato:regio.decreto:1942-03-16;262"
)
CODE_ARTICLE = re.compile(r"CODICE CIVILE-art\.\s*(\d+(?:/\d+)?(?:[- ][a-z]+)*(?:\.\d+)?)", re.I)
EDITION = re.compile(r"_VIGENZA_(\d{4}-\d{2}-\d{2})_", re.I)
BOOK_CHECKS = {"1", "456", "832", "1173", "1576", "2082", "2740", "2969"}
# AKN attachment labels and their printed headings differ for these articles.
HEADING_ALIASES = {
    "1159-bis": "1159",
    "2545-quindecies": "2545-quinquiesdecies",
    "2545-sexdecies": "2545-sexiesdecies",
    "2545-duodevicies": "2545-octiesdecies",
}


def read_export(path: Path, as_of: date) -> bytes:
    if path.suffix.lower() != ".zip":
        return path.read_bytes()
    with ZipFile(path) as archive:
        matches = [
            name for name in archive.namelist()
            if "042U0262" in name and name.lower().endswith(".xml")
        ]
        dated = []
        for name in matches:
            version = EDITION.search(name)
            if version:
                effective = date.fromisoformat(version[1])
                if effective <= as_of:
                    dated.append((effective, name))
        if dated:
            return archive.read(max(dated)[1])
        if len(matches) == 1 and not EDITION.search(matches[0]):
            return archive.read(matches[0])
    raise ValueError("No matching Civil Code edition in the archive. Supply the selected AKN XML.")


def normalize_article(number: str, element: ET.Element) -> dict | None:
    main_body = element.find("{*}mainBody")
    if main_body is None:
        return None
    raw = "\n\n".join("".join(p.itertext()) for p in main_body.iterfind(".//{*}p"))
    separator = r"[\s-]+"
    printed = HEADING_ALIASES.get(number, number)
    patterns = {separator.join(re.escape(part) for part in re.split(r"[- ]", value))
                for value in (number, printed)}
    number_pattern = "|".join(sorted(patterns, key=len, reverse=True))
    start = re.search(
        rf"(?im)^\s*(?:\(\(\s*)?Art\.\s*(?:{number_pattern})(?![\w/-]|\.\d)[ \t]*\.?",
        raw,
    )
    if start is None:
        return None

    body = raw[start.end():].strip()
    title_match = re.match(r"^(?:\(\(\s*)?\(([^()\n]+)\)\.?(?:\s*\)\))?\s*", body)
    title = title_match[1] if title_match else None
    if title_match:
        body = body[title_match.end():]
    body = re.split(r"(?im)^\s*-{6,}\s*\n\s*AGGIORNAMENTO\b", body, maxsplit=1)[0]
    if number == "2969":
        body = re.split(r"(?im)^\s*Roma, add[iì]", body, maxsplit=1)[0]
    paragraphs = [" ".join(part.split()) for part in re.split(r"\n\s*\n", body)]
    text = "\n\n".join(part for part in paragraphs if part)
    cleaned = text.lstrip("() ").upper()
    if not text or cleaned.startswith(("ARTICOLO ABROGATO", "ARTICOLO SOPPRESSO")):
        return None
    return {"article_number": number, "title": title, "text": text}


def convert(xml: bytes, as_of: date) -> dict:
    root = ET.fromstring(xml)
    expression = root.find("./{*}act/{*}meta/{*}identification/{*}FRBRExpression")
    uri = expression.find("{*}FRBRthis") if expression is not None else None
    if uri is None or "/regio_decreto/stato/1942-03-16/262/" not in uri.get("value", ""):
        raise ValueError("This AKN export is not the Italian Civil Code.")
    expression_date = re.search(r"/ita@(\d{4}-\d{2}-\d{2})/", uri.get("value", ""))
    effective = date.fromisoformat(expression_date[1]) if expression_date else None
    if effective and effective > as_of:
        raise ValueError("The AKN edition took effect after the requested snapshot date.")

    articles = {}
    for doc in root.findall(".//{*}attachment/{*}doc"):
        match = CODE_ARTICLE.fullmatch(doc.get("name", "").strip())
        if match:
            number = match[1].lower().replace(" ", "-")
            article = normalize_article(number, doc)
            if article:
                if number in articles:
                    raise ValueError(f"Duplicate Civil Code article {number}.")
                articles[number] = article
    if len(articles) < 2500 or not BOOK_CHECKS.issubset(articles):
        missing = ", ".join(sorted(BOOK_CHECKS.difference(articles)))
        raise ValueError(f"Incomplete Civil Code export ({len(articles)} articles, missing checks: {missing}).")
    return {
        "source": {
            "name": "Codice civile italiano",
            "kind": "civil_code",
            "publisher": "Normattiva",
            "url": SOURCE,
            "as_of": as_of.isoformat(),
            "notice": "Riproduzione non autentica e gratuita.",
        },
        "articles": list(articles.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = convert(read_export(args.export, args.as_of), args.as_of)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.output.suffix == ".gz":
        serialized = gzip.compress(serialized, mtime=0)
    args.output.write_bytes(serialized)
    print(f"Imported {len(payload['articles'])} articles into {args.output}")


if __name__ == "__main__":
    main()
