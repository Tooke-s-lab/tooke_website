#!/usr/bin/env python3
"""
Checks that news-data.js is valid before it can reach the live site.

Why this exists:
  news-data.js is edited by hand, and its failure mode is unusually cruel. The
  posts are one JSON array, so a single missing comma between } and { does not
  break ONE post — it makes the whole file unparseable, and news.js renders
  nothing. The news page goes silently empty. Nothing turns red, no error is
  visible to whoever pushed, and the person best placed to spot it is looking at
  a cached copy of the page that still looks fine.

  The same is true of a stray " inside the text, which ends the string early and
  produces a parse error a dozen lines further down.

  So the file gets parsed at build time, and a mistake fails the DEPLOY instead
  of blanking the page. This is the only thing standing between a typo and an
  empty news page, which is why it runs in build.sh rather than on demand.

Usage:  python scripts/check-news.py
Exit:   1 if the file is unusable, so it can gate a deploy.
"""

import json
import os
import re
import sys

DATA = "news-data.js"
PHOTOS = "assets/news"

WS = " \t\r\n"
COMMENT_OPEN = "/" + "*"
COMMENT_CLOSE = "*" + "/"


def check_js_wrapper(text):
    """Confirm the file is valid JavaScript AROUND the posts, not merely valid
    JSON inside them.

    Learned the hard way, by this checker passing a file that broke the site.
    The header comment contained the two characters that END a block comment, as
    an example in a sentence. The comment therefore closed early, the rest of
    the header was parsed as code, the browser threw before ever reaching the
    posts, and the news page was empty — while this script reported everything
    fine, because the JSON between the brackets was still perfect.

    So: everything before the assignment must be whitespace or CLOSED comments.
    Anything else means a comment ended where it was not supposed to.

    (Note the delimiters are built from COMMENT_OPEN/COMMENT_CLOSE above rather
    than typed literally. Writing them out here would close THIS docstring's
    enclosing comment in any editor that highlights by pattern — and, more to
    the point, is precisely the mistake being detected.)
    """
    m = re.search(r"(?:window\s*\.\s*)?__TOOKE_NEWS\s*=", text)
    if not m:
        return None                      # extract() reports the missing name

    prefix = text[:m.start()]
    i = 0
    while i < len(prefix):
        c = prefix[i]
        if c in WS:
            i += 1
        elif prefix.startswith("//", i):
            nl = prefix.find("\n", i)
            i = len(prefix) if nl == -1 else nl + 1
        elif prefix.startswith(COMMENT_OPEN, i):
            end = prefix.find(COMMENT_CLOSE, i + 2)
            if end == -1:
                return ("the header comment is never closed. It needs the "
                        "closing delimiter before the posts start.")
            i = end + 2
        elif prefix.startswith("window", i):
            i += len("window")
        else:
            stray = prefix[i:i + 70].strip().splitlines()
            stray = stray[0] if stray else ""
            return ("there is text before the posts that is not inside a "
                    "comment:\n"
                    "     %s\n"
                    "   The header comment was closed early — almost certainly "
                    "because the two characters that end a block comment appear "
                    "INSIDE it. Everything after that point is read as code and "
                    "the news page would be EMPTY." % stray)
    return None


def extract(text):
    """Pull the JSON array out of `window.__TOOKE_NEWS = [ ... ];`

    Sliced between the first [ after the assignment and the last ], rather than
    stripped of comments, because a comment-stripper that does not understand
    string literals would corrupt any post containing // in its text.
    """
    m = re.search(r"__TOOKE_NEWS\s*=", text)
    if not m:
        return None, ("could not find `window.__TOOKE_NEWS =` in the file. "
                      "That line must stay exactly as it is — it is how the "
                      "page finds the posts.")
    start = text.find("[", m.end())
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return None, ("the list of posts is missing its opening [ or closing ]. "
                      "Everything between them is the posts; both must be there.")
    return text[start:end + 1], None


def main():
    if not os.path.isfile(DATA):
        sys.exit("%s is missing — run this from the repo root." % DATA)

    raw = open(DATA, encoding="utf8").read()

    err = check_js_wrapper(raw)
    if err:
        print("NEWS: %s" % err)
        sys.exit(1)

    chunk, err = extract(raw)
    if err:
        print("NEWS: %s" % err)
        sys.exit(1)

    try:
        posts = json.loads(chunk)
    except json.JSONDecodeError as e:
        lines = chunk.splitlines()
        bad = lines[e.lineno - 1].strip() if 0 <= e.lineno - 1 < len(lines) else ""
        print("NEWS: %s could not be read — the news page would be EMPTY.\n" % DATA)
        print("   %s" % e.msg)
        if bad:
            print("   near: %s" % (bad[:90] + ("..." if len(bad) > 90 else "")))
        print()
        print("   The usual causes, in order of likelihood:")
        print("     - a missing comma between one post's } and the next {")
        print('     - a " inside your text that is not written as \\"')
        print("     - a real line break inside the text: paragraphs must be")
        print("       typed as the two characters \\n twice, not by pressing Enter")
        print("     - a trailing comma after the very last }")
        sys.exit(1)

    if not isinstance(posts, list):
        print("NEWS: the posts must be a list in [ square brackets ].")
        sys.exit(1)

    problems, warnings = [], []

    if not posts:
        warnings.append("there are no posts at all — the news page will show "
                        "its empty state.")

    seen_dates = {}
    for i, p in enumerate(posts):
        where = "post %d" % (i + 1)
        if not isinstance(p, dict):
            problems.append("%s is not a { ... } block." % where)
            continue

        title = str(p.get("title") or "").strip()
        where = "post %d (%s)" % (i + 1, title or "untitled")

        if not title:
            problems.append("%s has no title." % where)
        if not str(p.get("body") or "").strip():
            problems.append("%s has no body text." % where)

        date = str(p.get("date") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            problems.append("%s has date %r — it must be YYYY-MM-DD, e.g. "
                            "2026-09-02." % (where, date))
        else:
            y, m_, d = (int(x) for x in date.split("-"))
            if not (1 <= m_ <= 12 and 1 <= d <= 31):
                problems.append("%s has date %s, which is not a real date."
                                % (where, date))
            seen_dates.setdefault(date, []).append(title)

        photo = p.get("photo")
        alt = str(p.get("alt") or "").strip()
        if photo:
            path = os.path.join(PHOTOS, str(photo))
            if not os.path.isfile(path):
                problems.append("%s points at %s, which is not in %s/. Run "
                                "scripts/prepare-news-photo.py on your photo "
                                "first." % (where, photo, PHOTOS))
            elif not str(photo).lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
                problems.append("%s uses %s. Browsers cannot display that — "
                                "run scripts/prepare-news-photo.py on it."
                                % (where, photo))
            if not alt:
                problems.append("%s has a photo but no alt text. Describe the "
                                "picture for a reader who cannot see it; it is "
                                "required." % where)

        for field in ("title", "body", "alt"):
            val = str(p.get(field) or "")
            if re.search(r"\[[^\]]{12,}\]", val):
                warnings.append("%s still has placeholder text in its %s."
                                % (where, field))

    for date, titles in seen_dates.items():
        if len(titles) > 1:
            warnings.append("%d posts share the date %s; their order on the "
                            "page is then arbitrary." % (len(titles), date))

    for w in warnings:
        print("NEWS note: %s" % w)

    if problems:
        print()
        print("NEWS PROBLEMS (%d) — these would be wrong on the live site:"
              % len(problems))
        for p in problems:
            print("   - %s" % p)
        sys.exit(1)

    print("News OK: %d post%s, all readable."
          % (len(posts), "" if len(posts) == 1 else "s"))


if __name__ == "__main__":
    main()
