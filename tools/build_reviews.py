#!/usr/bin/env python3
"""Build reviews.html and the three sample-review pages from tools/content/*.md.

Run from anywhere:

    python3 tools/build_reviews.py

The supplied writing is converted, never edited. The only text transformation
is rewriting the absolute apply URL to the site-relative one. After editing a
source file under tools/content/, re-run this script and then
tools/verify_fidelity.py to confirm the pages still match the markdown
word for word.

Chassis CSS (design tokens, stage, grain, topbar, cursor, reduced-motion) is
lifted verbatim out of essays.html at build time, so the review pages cannot
drift from the rest of the site. Prose CSS for headings, lists, blockquotes
and rules is added on top, since essays.html only ever needed paragraphs.
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'content'
REPO = HERE.parent
ESSAYS = REPO / 'essays.html'

APPLY_ABS = 'https://nullifythepreset.com/apply.html'
APPLY_REL = 'apply.html'

REVIEWS = [
    ('01', 'sample-review-1-researched-for-weeks-still-stuck'),
    ('02', 'sample-review-2-one-piece-of-criticism'),
    ('03', 'sample-review-3-reopening-decisions'),
]

# ---------------------------------------------------------------- chassis CSS


def chassis():
    style = ESSAYS.read_text(encoding='utf-8').split('<style>', 1)[1].split('</style>', 1)[0]
    head = style.split('/* Catalog wrap */', 1)[0].rstrip()
    tail = '/* Custom cursor */' + style.split('/* Custom cursor */', 1)[1].rstrip()
    assert '--moss-light' in head and '.topbar' in head, 'chassis extraction failed'
    assert '.cursor-ring' in tail, 'cursor extraction failed'
    return head, tail


HEAD_CSS, TAIL_CSS = chassis()

# ---------------------------------------------------------------- markdown

LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def inline(s: str) -> str:
    """Escape, then apply links, bold and italic (in that order)."""
    s = html.escape(s, quote=False)
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

BACK_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">'
            '<path d="M19 12H5M12 19l-7-7 7-7"/></svg>')

ARROW_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true">'
             '<path d="M5 12h14M12 5l7 7-7 7"/></svg>')

DOC_CSS = """
/* ─── Document page (sample reviews) ─── */
.doc-wrap{
  position: relative; z-index: 2;
  max-width: 68ch; margin: 0 auto;
  padding: clamp(120px, 18vh, 160px) var(--pad-x) clamp(80px, 12vw, 120px);
}
.back-link{
  display: flex; width: fit-content;
  align-items: center; gap: 8px;
  font-family: var(--mono);
  font-size: clamp(10px, 0.7vw, 11px);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--ink-muted);
  text-decoration: none;
  margin-bottom: clamp(36px, 5vw, 56px);
  transition: color 0.3s ease, transform 0.3s ease;
}
.back-link:hover{ color: var(--ink); transform: translateX(-4px); }
.back-link:focus-visible{ outline: 1px solid var(--moss-light); outline-offset: 6px; }

.doc-wrap .label{
  font-family: var(--mono);
  font-size: clamp(10px, 0.65vw, 11px);
  letter-spacing: 0.22em;
  color: var(--ink-muted);
  text-transform: uppercase;
  display: inline-block;
  margin-bottom: clamp(14px, 1.8vw, 18px);
}
.doc-wrap h1{
  font-family: var(--serif);
  font-weight: 300;
  font-size: clamp(1.9rem, 4.4vw, 2.7rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin-bottom: clamp(28px, 3.6vw, 38px);
  text-wrap: balance;
}

/* The hypothetical-case notice. Must stay visible in any layout. */
.hypothetical{
  margin: 0 0 clamp(40px, 5vw, 56px);
  padding: clamp(18px, 2.2vw, 24px) clamp(20px, 2.4vw, 26px);
  border: 1px solid var(--rule-green);
  border-left: 2px solid var(--moss-light);
  border-radius: var(--rad);
  background:
    radial-gradient(circle at 0% 0%, rgba(110, 142, 123, 0.10), transparent 70%),
    rgba(235, 229, 214, 0.028);
  font-family: var(--sans);
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--ink-soft);
}
.hypothetical strong{ color: var(--ink); font-weight: 600; }

.doc-body h2{
  font-family: var(--serif);
  font-weight: 300;
  font-size: clamp(1.3rem, 2.2vw, 1.6rem);
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin: clamp(44px, 5.5vw, 64px) 0 clamp(16px, 2vw, 22px);
  text-wrap: balance;
}
.doc-body h2:first-child{ margin-top: 0; }
.doc-body p{
  font-family: var(--sans);
  font-weight: 400;
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--ink-soft);
  margin: 0 0 1.15em;
}
.doc-body strong{ color: var(--ink); font-weight: 600; }
.doc-body em{ font-style: italic; }
.doc-body a{
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--rule-strong);
  text-underline-offset: 3px;
  transition: text-decoration-color 0.3s ease;
}
.doc-body a:hover{ text-decoration-color: var(--moss-light); }

.doc-body ul, .doc-body ol{
  margin: 0 0 1.15em;
  padding-left: 1.5em;
  color: var(--ink-soft);
  font-size: 1.05rem;
  line-height: 1.75;
}
.doc-body li{ margin-bottom: 0.6em; }
.doc-body li::marker{ color: var(--ink-muted); }
.doc-body ol > li::marker{ font-family: var(--mono); font-size: 0.85em; }

.doc-body blockquote{
  margin: 0 0 1.4em;
  padding-left: clamp(16px, 2vw, 22px);
  border-left: 1px solid var(--rule-green);
  color: var(--ink-soft);
  font-size: 1.02rem;
  line-height: 1.75;
}

.doc-body hr{
  border: 0;
  border-top: 1px solid var(--rule);
  margin: clamp(44px, 5.5vw, 64px) 0;
}

.doc-body p.note{
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--ink-muted);
  font-style: italic;
}

/* Closing invitation */
.closing{
  margin-top: clamp(48px, 6vw, 72px);
  padding: clamp(24px, 3vw, 34px) clamp(22px, 2.8vw, 32px);
  border: 1px solid var(--rule-green);
  border-radius: var(--rad);
  background:
    radial-gradient(circle at 50% 0%, rgba(110, 142, 123, 0.12), transparent 70%),
    rgba(235, 229, 214, 0.04);
}
.closing p{
  font-family: var(--sans);
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--ink-soft);
  margin: 0;
}
.closing strong{ color: var(--ink); font-weight: 600; }
.closing a{
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--moss-light);
  text-underline-offset: 3px;
}
.closing a:hover{ text-decoration-color: var(--ink); }

/* Sequential nav between reviews */
.doc-nav{
  margin-top: clamp(40px, 5vw, 56px);
  padding-top: clamp(24px, 3vw, 32px);
  border-top: 1px solid var(--rule);
  display: flex; flex-wrap: wrap; gap: 16px 28px;
  justify-content: space-between; align-items: center;
  font-family: var(--mono);
  font-size: clamp(10px, 0.7vw, 11px);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
.doc-nav a{
  display: inline-flex; align-items: center; gap: 8px;
  color: var(--ink-muted); text-decoration: none;
  transition: color 0.3s ease;
}
.doc-nav a:hover{ color: var(--ink); }
.doc-nav a:focus-visible{ outline: 1px solid var(--moss-light); outline-offset: 6px; }
"""

INDEX_CSS = """
/* ─── Reviews index ─── */
.reviews-wrap{
  position: relative; z-index: 2;
  max-width: 760px; margin: 0 auto;
  padding: clamp(120px, 18vh, 160px) var(--pad-x) clamp(80px, 12vw, 120px);
}
.reviews-header{ text-align: center; margin-bottom: clamp(40px, 5vw, 56px); }
.reviews-header h1{
  font-family: var(--serif);
  font-weight: 300;
  font-size: clamp(2.4rem, 7vw, 4.2rem);
  line-height: 1;
  letter-spacing: -0.025em;
  color: var(--ink);
}
.reviews-intro{ margin-bottom: clamp(56px, 7vw, 80px); }
.reviews-intro p{
  font-family: var(--sans);
  font-size: 1.05rem;
  line-height: 1.75;
  color: var(--ink-soft);
  margin: 0 0 1.15em;
}
.reviews-intro p:last-child{ margin-bottom: 0; }

.reviews-list{ border-top: 1px solid var(--rule); }
.review-row{
  display: grid;
  grid-template-columns: auto 1fr;
  gap: clamp(20px, 3vw, 36px);
  padding: clamp(24px, 3vw, 32px) 0;
  border-bottom: 1px solid var(--rule);
  color: var(--ink-soft);
  text-decoration: none;
  transition: color 0.3s ease, transform 0.3s ease;
}
.review-row:hover{ color: var(--ink); transform: translateX(-4px); }
.review-row:focus-visible{ outline: 1px solid var(--moss-light); outline-offset: 6px; }
.review-idx{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.2em;
  color: var(--ink-muted);
  padding-top: 0.45em;
}
.review-title{
  font-family: var(--serif);
  font-weight: 300;
  font-size: clamp(1.15rem, 1.8vw, 1.4rem);
  line-height: 1.3;
  color: var(--ink);
  display: block;
  margin-bottom: 8px;
  text-wrap: balance;
}
.review-desc{
  font-family: var(--sans);
  font-size: 0.94rem;
  line-height: 1.65;
  color: var(--ink-muted);
  display: block;
}

/* Index apply CTA */
.index-cta{
  margin-top: clamp(56px, 7vw, 80px);
  text-align: center;
}
.index-cta .cta{
  display: inline-flex; align-items: center; gap: 12px;
  padding: 17px 30px;
  border-radius: var(--rad);
  background: var(--ink);
  color: var(--bg);
  font-family: var(--mono);
  font-size: clamp(10px, 0.72vw, 11.5px);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  text-decoration: none;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.index-cta .cta:hover{
  transform: translateY(-2px);
  box-shadow: 0 18px 40px -18px rgba(0, 0, 0, 0.7);
}
.index-cta .cta:focus-visible{ outline: 1px solid var(--moss-light); outline-offset: 5px; }
.index-cta .foot{
  display: block;
  margin-top: 18px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ink-muted);
}
"""

SCRIPT_JS = """
  let lenis = null;
  try {
    if (typeof Lenis !== 'undefined' && !window.__noLenis) {
      lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        direction: 'vertical',
        smooth: true,
      });
      function raf(t){ lenis.raf(t); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
    }
  } catch (e) { lenis = null; }

  const topbar = document.getElementById('topbar');
  function onScroll(){
    if (window.scrollY > 24) topbar.classList.add('scrolled');
    else topbar.classList.remove('scrolled');
  }
  if (lenis) lenis.on('scroll', onScroll);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const dot = document.getElementById('cursorDot');
  const ring = document.getElementById('cursorRing');
  let mx = -100, my = -100, rx = mx, ry = my;
  dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%, -50%)`;
  ring.style.transform = `translate(${mx}px, ${my}px) translate(-50%, -50%)`;
  addEventListener('mousemove', (e) => {
    mx = e.clientX; my = e.clientY;
    dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%, -50%)`;
  });
  function ringLoop(){
    rx += (mx - rx) * 0.18; ry += (my - ry) * 0.18;
    ring.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%)`;
    requestAnimationFrame(ringLoop);
  }
  ringLoop();
  document.querySelectorAll('a, button').forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('hover'));
    el.addEventListener('mouseleave', () => ring.classList.remove('hover'));
  });
"""


def shell(title, extra_css, back_href, back_label, body):
    return f"""<!DOCTYPE html>
<html lang="en" class="lenis">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0A100D">
<title>{html.escape(title)}</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,200;0,300;0,400;1,300;1,400&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">

<script src="https://unpkg.com/@studio-freight/lenis@1.0.34/dist/lenis.min.js" onerror="window.__noLenis=true"></script>

<style>
{HEAD_CSS}

{extra_css.strip()}

{TAIL_CSS}
</style>
</head>
<body>

<div class="stage" aria-hidden="true"></div>
<div class="grain" aria-hidden="true"></div>
<div class="cursor-ring" id="cursorRing"></div>
<div class="cursor-dot" id="cursorDot"></div>

<header class="topbar" id="topbar">
  <a class="mark" href="index.html">
    <span class="glyph"></span>
    <span>Nullify the Preset</span>
  </a>
  <a href="{back_href}" class="back">
    {BACK_SVG}
    {back_label}
  </a>
</header>

{body}

<script>
{SCRIPT_JS.strip()}
</script>
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
    nav.append(f'<a href="{prev_slug}.html">{BACK_SVG} Previous review</a>'
               if prev_slug else '<span></span>')
    nav.append(f'<a href="{next_slug}.html">Next review {ARROW_SVG}</a>'
               if next_slug else f'<a href="reviews.html">All reviews {ARROW_SVG}</a>')

    body = f"""<main class="doc-wrap">
  <a class="back-link" href="reviews.html">{BACK_SVG} Back to sample reviews</a>
  <span class="label">{html.escape(label)}</span>
  <h1>{inline(h1)}</h1>

  <aside class="hypothetical" role="note">{inline(quote)}</aside>

  <article class="doc-body">
    {render_body(body_blocks)}
  </article>

  <div class="closing">
    <p>{inline(closing)}</p>
  </div>

  <nav class="doc-nav">
    {nav[0]}
    {nav[1]}
  </nav>
</main>"""

    page_title = re.sub(r'\*+', '', h1).strip().strip('"“”') + ' — Nullify the Preset'
    out = REPO / f'{slug}.html'
    out.write_text(shell(page_title, DOC_CSS, 'reviews.html', 'Reviews', body), encoding='utf-8')
    return out, h1


def build_index(entries, intro, descs):
    rows = []
    for idx, slug, title in entries:
        desc = descs.get(slug)
        assert desc, f'no index blurb for {slug} in website-integration-copy.md'
        rows.append(
            f'    <a class="review-row" href="{slug}.html">\n'
            f'      <span class="review-idx">{idx}</span>\n'
            f'      <span>\n'
            f'        <span class="review-title">{inline(title)}</span>\n'
            f'        <span class="review-desc">{inline(desc)}</span>\n'
            f'      </span>\n'
            f'    </a>'
        )

    body = f"""<main class="reviews-wrap">
  <div class="reviews-header">
    <h1>Sample Reviews</h1>
  </div>

  <div class="reviews-intro">
    {chr(10).join('    <p>' + inline(p) + '</p>' for p in intro).strip()}
  </div>

  <div class="reviews-list">
{chr(10).join(rows)}
  </div>

  <div class="index-cta">
    <a class="cta" href="apply.html">
      Apply for a Private Review
      {ARROW_SVG}
    </a>
    <span class="foot">Free · Async · Structured</span>
  </div>
</main>"""

    out = REPO / 'reviews.html'
    out.write_text(shell('Sample Reviews — Nullify the Preset', INDEX_CSS,
                         'index.html', 'Back', body), encoding='utf-8')
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
