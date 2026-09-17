# tools

Build scripts for the sample-review pages.

## What this is for

`reviews.html` and the three `sample-review-*.html` pages are **generated**, not
hand-edited. Their prose comes from the markdown in `content/`, and the page
chassis (design tokens, stage, grain, topbar, cursor, reduced-motion rules) is
lifted out of `essays.html` at build time so the review pages cannot drift from
the rest of the site.

Editing the generated HTML directly means your change is lost the next time
anyone runs the build. Edit the markdown instead.

## Usage

```sh
python3 tools/build_reviews.py     # regenerate the four pages
python3 tools/verify_fidelity.py   # confirm they still match the markdown
```

No dependencies beyond the Python 3 standard library. Both scripts can be run
from any directory.

## Editing the content

| To change | Edit |
|---|---|
| A review's title or body | `content/sample-review-*.md` |
| The index intro paragraphs | `content/website-integration-copy.md`, under `### Sample Reviews` |
| A review's one-line index blurb | `content/website-integration-copy.md`, under `## Resource descriptions` |

Then re-run both scripts.

## Why the fidelity check exists

The review copy is final and is meant to be converted verbatim, never
rewritten. `verify_fidelity.py` strips markup from both the markdown and the
built HTML, then compares the two word streams. It exits non-zero on any
divergence and prints the first one, so an accidental edit to a generated page
— or a conversion bug — shows up immediately instead of shipping.

It tolerates exactly one intentional difference: the `A sample private review`
line is hoisted above the `h1` to serve as an eyebrow label, so its position in
the stream differs from the source.

## Things worth knowing

- **The hypothetical notice is load-bearing.** Each review's
  `> **This case is hypothetical.** …` blockquote is rendered into a bordered
  callout between the title and the body, deliberately outside the scrollable
  article, so it cannot be collapsed or styled away. Per the author's note:
  a reader who suspects the cases are disguised real clients trusts the method
  less, not more.
- **Apply links.** The markdown uses the absolute
  `https://nullifythepreset.com/apply.html`. The build rewrites it to the
  relative `apply.html`, matching every other link in the site and surviving
  being served from a subpath. This is the only text transformation applied.
- **Worksheet.** The "Before You Reopen the Decision" worksheet was removed
  from this section; it belongs somewhere else on the site. Its source
  markdown and the two PDFs are recoverable from git history if it comes back.
  Note that review 3's prose still refers to it ("the worksheet on this site is
  built for this", "the completed worksheet example uses a 5% gap"), so those
  two sentences currently point at something not published.
- **`content/` is not served.** The markdown is kept for editing and for the
  fidelity check. The public pages are the generated HTML at the repo root.
