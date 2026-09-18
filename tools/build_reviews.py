#!/usr/bin/env python3
"""Build reviews.html and the three sample-review pages from tools/content/*.md.

Run from anywhere:

    python3 tools/build_reviews.py

The supplied writing is converted, never edited. The only text transformation
is rewriting the absolute apply URL to the site-relative one. After editing a
source file under tools/content/, re-run this script and then
tools/verify_fidelity.py to confirm the pages still match the markdown
word for word.

Every page links the shared site.css / site.js, so the review pages cannot
drift from the rest of the site. Only the two small page-specific rule sets
below are inlined.
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'content'
REPO = HERE.parent

APPLY_ABS = 'https://nullifythepreset.com/apply.html'
APPLY_REL = 'apply.html'

REVIEWS = [
    ('01', 'sample-review-1-researched-for-weeks-still-stuck'),
    ('02', 'sample-review-2-one-piece-of-criticism'),
    ('03', 'sample-review-3-reopening-decisions'),
]

# ---------------------------------------------------------------- markdown

LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def smarten(s: str) -> str:
    """Straight quotes -> typographic quotes. Words are untouched, so the
    fidelity check (which folds quote styles) still sees identical prose."""
    s = re.sub(r'(^|[\s(\[\u2014-])"', '\\1\u201c', s)
    s = s.replace('"', '\u201d')
    s = re.sub(r"(^|[\s(\[\u2014])'(?=\w)", '\\1\u2018', s)
    s = s.replace("'", '\u2019')
    return s


def inline(s: str) -> str:
    """Escape, then apply links, bold and italic (in that order)."""
    s = html.escape(smarten(s), quote=False)
    s = LINK_RE.sub(
        lambda m: '<a href="{}">{}</a>'.format(
            m.group(2).replace(APPLY_ABS, APPLY_REL), m.group(1)),
        s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s, flags=re.S)
    s = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\s*\n\s*', ' ', s)
    return s.strip()


def blocks(md: str):
    """Split markdown into (kind, payload) blocks."""
    out = []
    for raw in re.split(r'\n\s*\n', md.strip()):
        b = raw.strip()
        if not b:
            continue
        if re.fullmatch(r'-{3,}', b):
            out.append(('hr', ''))
        elif b.startswith('# '):
            out.append(('h1', b[2:].strip()))
        elif b.startswith('## '):
            out.append(('h2', b[3:].strip()))
        elif b.startswith('> '):
            out.append(('quote', ' '.join(
                ln.lstrip('> ').strip() for ln in b.split('\n'))))
        elif re.match(r'^\d+\.\s', b):
            items = re.split(r'\n(?=\d+\.\s)', b)
            out.append(('ol', [re.sub(r'^\d+\.\s*', '', i).strip() for i in items]))
        elif b.startswith('- '):
            items = re.split(r'\n(?=- )', b)
            out.append(('ul', [i[2:].strip() for i in items]))
        else:
            out.append(('p', b))
    return out


def render_body(bs) -> str:
    """Emit the article body. Drops a leading rule and collapses runs."""
    parts = []
    for kind, payload in bs:
        if kind == 'hr':
            if not parts or parts[-1] == '<hr>':
                continue
            parts.append('<hr>')
        elif kind == 'h2':
            parts.append(f'<h2>{inline(payload)}</h2>')
        elif kind == 'quote':
            parts.append(f'<blockquote>{inline(payload)}</blockquote>')
        elif kind == 'ol':
            lis = '\n'.join(f'      <li>{inline(i)}</li>' for i in payload)
            parts.append(f'<ol>\n{lis}\n    </ol>')
        elif kind == 'ul':
            lis = '\n'.join(f'      <li>{inline(i)}</li>' for i in payload)
            parts.append(f'<ul>\n{lis}\n    </ul>')
        else:
            cls = ' class="note"' if payload.startswith('*') and payload.rstrip().endswith('*') else ''
            parts.append(f'<p{cls}>{inline(payload)}</p>')
    while parts and parts[-1] == '<hr>':
        parts.pop()
    return '\n    '.join(parts)


def integration_copy():
    """Pull the index intro and the per-review blurbs out of
    website-integration-copy.md, so that copy lives in exactly one place."""
    md = (SRC / 'website-integration-copy.md').read_text(encoding='utf-8')

    sec = md.split('### Sample Reviews', 1)[1].split('\n---', 1)[0]
    intro = [' '.join(p.split()) for p in re.split(r'\n\s*\n', sec.strip()) if p.strip()]
    assert len(intro) == 3, f'expected 3 intro paragraphs, got {len(intro)}'

    descs = {}
    for m in re.finditer(
            r'\*\*\[([^\]]+)\]\(([^)]+)\.html\)\*\*\s*\n(.+?)(?=\n\s*\n|\Z)', md, re.S):
        descs[m.group(2)] = ' '.join(m.group(3).split())

    return intro, descs


# ---------------------------------------------------------------- page shell

ARROW_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M5 12h14M12 5l7 7-7 7"/></svg>')

DOC_CSS = """
.doc-wrap > .label{ display: inline-flex; }
"""

INDEX_CSS = """
.reviews .row{ grid-template-columns: auto 1fr auto; }
.reviews .row .title{ font-size: clamp(1.3rem, 2vw, 1.75rem); }
.reviews .row .desc{ font-size: 0.97rem; color: var(--ink-soft); margin-top: 12px; }
.reviews .row .idx{ padding-top: 0.5em; }
.reviews .cta-cluster{ margin-top: clamp(44px, 6vw, 72px); }
.reviews .write-line{ margin-top: 22px; }
"""

FONTS = ('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,200;0,300;0,400;1,300;1,400'
         '&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400&display=swap')


def topbar():
    return f"""<header class="topbar" id="topbar">
  <a class="mark" href="index.html" aria-label="Nullify the Preset — home">
    <span class="glyph"></span>
    <span>Nullify the Preset</span>
  </a>
  <nav aria-label="Site">
    <a href="essays.html">Essays <span class="count">20</span></a>
    <a href="reviews.html" aria-current="page">Reviews <span class="count">03</span></a>
    <a href="apply.html" class="apply">Apply {ARROW_SVG}</a>
  </nav>
</header>"""


FOOTER = """<footer class="site">
  <div class="inner">
    <div class="cols">
      <div>
        <a class="brand" href="index.html">
          <svg width="40" height="40" viewBox="0 0 48 48" fill="none" aria-hidden="true">
            <circle cx="24" cy="24" r="22" stroke="rgba(235,229,214,0.5)" stroke-width="1"/>
            <circle cx="24" cy="24" r="10" stroke="rgba(235,229,214,0.4)" stroke-width="1"/>
            <circle cx="24" cy="24" r="3" fill="#6E8E7B"/>
            <line x1="24" y1="2" x2="24" y2="14" stroke="rgba(235,229,214,0.4)" stroke-width="1"/>
            <line x1="24" y1="34" x2="24" y2="46" stroke="rgba(235,229,214,0.4)" stroke-width="1"/>
            <line x1="2" y1="24" x2="14" y2="24" stroke="rgba(235,229,214,0.4)" stroke-width="1"/>
            <line x1="34" y1="24" x2="46" y2="24" stroke="rgba(235,229,214,0.4)" stroke-width="1"/>
          </svg>
          <span class="name">Nullify the Preset</span>
        </a>
        <p class="tag">A diagnostic for the mind that multiplies. Free, async, structurally precise.</p>
      </div>
      <div>
        <h4>Read</h4>
        <ul>
          <li><a href="essays.html">Essays <span class="count">20</span></a></li>
          <li><a href="reviews.html">Sample Reviews <span class="count">03</span></a></li>
          <li><a href="apply.html">Apply for a Private Review</a></li>
        </ul>
      </div>
      <div>
        <h4>Write</h4>
        <a class="mail" href="mailto:official@nullifythepreset.com">official@nullifythepreset.com</a>
        <p class="mail-note">Questions before applying go here. Applications go through the form.</p>
      </div>
    </div>
    <div class="bottom">
      <span>Private<span class="sep">·</span>Async<span class="sep">·</span>By application only</span>
      <span>© <span data-year>2026</span> Nullify the Preset</span>
    </div>
  </div>
</footer>"""


def shell(title, extra_css, body, description=''):
    return f"""<!DOCTYPE html>
<html lang="en" class="lenis">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0A100D">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="site.css">

<style>
{extra_css.strip()}
</style>
</head>
<body>

<div class="stage" aria-hidden="true"></div>
<div class="grain" aria-hidden="true"></div>
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="cursor-ring" id="cursorRing" aria-hidden="true"></div>
<div class="cursor-dot" id="cursorDot" aria-hidden="true"></div>

{topbar()}

{body}

{FOOTER}

<script src="https://unpkg.com/@studio-freight/lenis@1.0.34/dist/lenis.min.js" onerror="window.__noLenis=true"></script>
<script src="site.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- build pages

def build_review(slug, prev_slug, next_slug):
    md = (SRC / f'{slug}.md').read_text(encoding='utf-8')
    bs = blocks(md)

    h1 = next(p for k, p in bs if k == 'h1')
    subtitle = next((p for k, p in bs if k == 'p' and 'sample private review' in p.lower()), None)
    quote = next(p for k, p in bs if k == 'quote')

    closing = None
    body_blocks = []
    for k, p in bs:
        if k == 'h1':
            continue
        if k == 'p' and p is subtitle:
            continue
        if k == 'quote' and p is quote:
            continue
        if k == 'p' and APPLY_ABS in p:
            closing = p
            continue
        body_blocks.append((k, p))

    assert closing, f'{slug}: closing invitation not found'

    label = re.sub(r'\*+', '', subtitle).strip() if subtitle else 'A sample private review'

    nav = []
    nav.append(f'<a class="arrow-link back" href="{prev_slug}.html">{ARROW_SVG} Previous review</a>'
               if prev_slug else '<span></span>')
    nav.append(f'<a class="arrow-link" href="{next_slug}.html">Next review {ARROW_SVG}</a>'
               if next_slug else f'<a class="arrow-link" href="reviews.html">All reviews {ARROW_SVG}</a>')

    body = f"""<main class="doc-wrap">
  <a class="arrow-link back" href="reviews.html">{ARROW_SVG} Back to sample reviews</a>
  <span class="label">{html.escape(label)}</span>
  <h1>{inline(h1)}</h1>

  <aside class="hypothetical" role="note">{inline(quote)}</aside>

  <article class="doc-body">
    {render_body(body_blocks)}
  </article>

  <div class="closing">
    <p>{inline(closing)}</p>
  </div>

  <nav class="doc-nav" aria-label="Review navigation">
    {nav[0]}
    {nav[1]}
  </nav>
</main>"""

    page_title = re.sub(r'\*+', '', h1).strip().strip('"“”') + ' — Nullify the Preset'
    out = REPO / f'{slug}.html'
    out.write_text(shell(page_title, DOC_CSS, body, 'A full sample private review, published so the method can be inspected before you apply.'), encoding='utf-8')
    return out, h1


def build_index(entries, intro, descs):
    rows = []
    for idx, slug, title in entries:
        desc = descs.get(slug)
        assert desc, f'no index blurb for {slug} in website-integration-copy.md'
        rows.append(
            f'    <a class="row" href="{slug}.html">\n'
            f'      <span class="idx">{idx}</span>\n'
            f'      <span>\n'
            f'        <span class="title">{inline(title)}</span>\n'
            f'        <span class="desc">{inline(desc)}</span>\n'
            f'      </span>\n'
            f'      <span class="go">{ARROW_SVG}</span>\n'
            f'    </a>'
        )

    lede = chr(10).join('      <p>' + inline(p) + '</p>' for p in intro)
    body = f"""<main class="index-wrap reviews">
  <div class="index-head">
    <div>
      <span class="label">Sample Reviews <span class="tick">·</span> Three cases</span>
      <h1>Sample Reviews</h1>
    </div>
    <div class="lede">
{lede}
    </div>
  </div>

  <div class="rows">
{chr(10).join(rows)}
  </div>

  <div class="cta-cluster">
    <a class="cta" href="apply.html" data-magnetic>
      <span>Apply for a Private Review</span>
      {ARROW_SVG}
    </a>
    <span class="label bare center">Free <span class="tick">·</span> Async <span class="tick">·</span> Structured</span>
    <p class="write-line">Questions before you apply? <a href="mailto:official@nullifythepreset.com">official@nullifythepreset.com</a></p>
  </div>
</main>"""

    out = REPO / 'reviews.html'
    out.write_text(shell('Sample Reviews — Nullify the Preset', INDEX_CSS, body,
                         'Three full-length sample private reviews. Read the method before you apply.'),
                   encoding='utf-8')
    return out


def main():
    intro, descs = integration_copy()

    entries = []
    for i, (idx, slug) in enumerate(REVIEWS):
        prev_slug = REVIEWS[i - 1][1] if i > 0 else None
        next_slug = REVIEWS[i + 1][1] if i + 1 < len(REVIEWS) else None
        out, title = build_review(slug, prev_slug, next_slug)
        entries.append((idx, slug, title))
        print(f'built {out.name} ({out.stat().st_size // 1024} KB)')

    out = build_index(entries, intro, descs)
    print(f'built {out.name} ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
