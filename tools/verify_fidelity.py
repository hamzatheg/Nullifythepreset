#!/usr/bin/env python3
"""Verify the generated review pages contain exactly the source prose.

Run from anywhere:

    python3 tools/verify_fidelity.py

Strips markup from the source markdown and from the built HTML, normalises
whitespace, and compares the two word streams. Exits non-zero on any
divergence and prints where it starts. Use this after editing anything under
tools/content/ and re-running tools/build_reviews.py, to confirm the pages
are still a faithful conversion rather than an edit.
"""

import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'content'
REPO = HERE.parent

SLUGS = [
    'sample-review-1-researched-for-weeks-still-stuck',
    'sample-review-2-one-piece-of-criticism',
    'sample-review-3-reopening-decisions',
]

# Hoisted above the h1 as an eyebrow label, so its position differs by design.
LABEL = 'A sample private review'.split()


def md_words(md: str):
    t = md
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)    # links -> text
    t = re.sub(r'^\s*-{3,}\s*$', ' ', t, flags=re.M)  # horizontal rules
    t = re.sub(r'^#{1,6}\s*', '', t, flags=re.M)      # headings
    t = re.sub(r'^\s*>\s?', '', t, flags=re.M)        # blockquotes
    t = re.sub(r'^\s*[-*]\s+', '', t, flags=re.M)     # bullets
    t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.M)    # numbers
    t = t.replace('**', '').replace('*', '')          # emphasis
    return t.split()


def html_words(doc: str):
    body = doc.split('<main', 1)[1].split('>', 1)[1].rsplit('</main>', 1)[0]
    body = re.sub(r'<nav class="doc-nav".*?</nav>', ' ', body, flags=re.S)
    body = re.sub(r'<a class="arrow-link back".*?</a>', ' ', body, flags=re.S)
    body = re.sub(r'<svg.*?</svg>', ' ', body, flags=re.S)
    body = re.sub(r'<[^>]+>', ' ', body)
    # The build sets typographic quotes; fold them back so only the words are compared.
    body = html.unescape(body).translate(str.maketrans('\u201c\u201d\u2018\u2019', '""\'\''))
    return body.split()


def drop_label(ws):
    n = len(LABEL)
    for i in range(len(ws) - n + 1):
        if ws[i:i + n] == LABEL:
            return ws[:i] + ws[i + n:]
    return ws


def main():
    failures = 0
    for slug in SLUGS:
        md_path = SRC / f'{slug}.md'
        page_path = REPO / f'{slug}.html'
        if not md_path.exists() or not page_path.exists():
            print(f'MISS {slug}: missing source or built page')
            failures += 1
            continue

        want = drop_label(md_words(md_path.read_text(encoding='utf-8')))
        got = drop_label(html_words(page_path.read_text(encoding='utf-8')))

        if want == got:
            print(f'OK   {slug}  ({len(want)} words, exact match)')
            continue

        i = 0
        while i < min(len(want), len(got)) and want[i] == got[i]:
            i += 1
        print(f'FAIL {slug}')
        print(f'     source {len(want)} words, page {len(got)} words')
        print(f'     first divergence at word {i}:')
        print(f'       source: {" ".join(want[max(0, i - 6):i + 10])!r}')
        print(f'       page  : {" ".join(got[max(0, i - 6):i + 10])!r}')
        failures += 1

    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
