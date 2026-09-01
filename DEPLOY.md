# Deploying the site

The site is static. There is no framework, no bundler, and no npm. Cloudflare
Pages watches the GitHub repo, runs one short shell script, and serves the result.

---

## One-time setup

### 1. Create the GitHub repo

Make an **empty private repo** called `tooke-lab-site` at
<https://github.com/new>. Do **not** tick "Add a README" — the repo already has
one, and an initial commit on the GitHub side means the first push is rejected
for unrelated histories.

### 2. Push this folder to it

From `C:\Users\drysd\Documents\tooke-lab-site`:

```bash
git remote add origin https://github.com/<your-username>/tooke-lab-site.git
git push -u origin main
```

The first push asks for GitHub credentials. Use a **personal access token** as
the password, not your account password — GitHub stopped accepting passwords over
HTTPS in 2021. Generate one at Settings → Developer settings → Personal access
tokens → Tokens (classic), with the `repo` scope.

### 3. Connect Cloudflare Pages

<https://dash.cloudflare.com> → **Workers & Pages** → **Create** → **Pages** →
**Connect to Git**.

Authorise the Cloudflare GitHub App. Because the repo is **private**, you must
explicitly grant it access to `tooke-lab-site` — "All repositories" also works,
but "Only select repositories" is the tighter choice.

Then set:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Framework preset | **None** |
| Build command | `sh build.sh` |
| Build output directory | `_site` |
| Root directory | *(leave blank)* |

Nothing else needs changing. There are no environment variables and no build
dependencies — `build.sh` copies files and runs a Python script that imports only
the standard library.

The first deploy lands on `https://tooke-lab-site.pages.dev`.

### 4. Custom domain (optional, later)

Pages project → **Custom domains** → **Set up a domain**. If the domain is on
Cloudflare DNS the records are written for you; otherwise you add the CNAME they
show you at your registrar. HTTPS is automatic either way.

A university subdomain (`tookelab.bath.ac.uk`) needs Bath IT to add the CNAME —
worth asking early, as that is usually the long pole.

---

## Everyday use

```bash
git add -A
git commit -m "what changed"
git push
```

Every push to `main` deploys, usually in well under a minute. Every push to any
other branch gets its own preview URL, which is the safe way to show Cat a change
before it is live:

```bash
git checkout -b new-photos
# ...edit...
git commit -am "swap the people hero"
git push -u origin new-photos      # -> a preview URL, main untouched
```

Rolling back is a click: Pages project → **Deployments** → find the last good
one → **Rollback**.

---

## What actually gets published

`build.sh` stages `_site/` and Cloudflare serves only that. It deliberately
leaves behind:

- `scripts/` — the build toolchain
- `serve.cmd`, `build.sh` — developer entry points
- `README.md`, `DEPLOY.md`, `HOW-TO-POST-NEWS.md`,
  `HOW-TO-CHANGE-A-PHOTO.md` — developer documentation
- `incoming/` — raw uploads waiting to be converted, and normally empty
- `.github/` — the workflow that converts them

That last group is the reason the staging step exists at all. Deploying the repo
root verbatim would put every one of these files on the public site, fetchable at
`tookelab.pages.dev/README.md` by anyone who guessed the filename.

**If you add a new top-level file that the site needs, add it to `build.sh`.**
The copy list is explicit — `*.html *.css *.js *.json` plus `assets/` — so a new
`.txt`, `.pdf`, `.xml` or `.webmanifest` at the root will pass every local test
and be silently missing in production. `scripts/check-links.py` runs inside the
build and will catch it if a page references it.

---

## If a deploy fails

Read the build log in the Pages dashboard. Realistically it is one of:

- **`check-links.py` exited 1.** A page references a file that is not committed.
  The log names the page and the reference. This is the gate working — fix the
  reference or commit the file.
- **`check-news.py` exited 1.** `news-data.js` will not parse, or a post is
  missing something. Usually a comma between `}` and `{`, or a `"` inside the
  text that is not written `\"`. The log names the post and the cause. Also the
  gate working: the alternative is a live news page that is silently empty.
- **`build.sh: not found`.** The build command lost its `sh ` prefix.
- **Nothing deployed, no error.** Build output directory is not `_site`.

To reproduce the whole thing locally before pushing:

```bash
sh build.sh
cd _site && python -m http.server 8912
```

That is byte-for-byte what Cloudflare will serve.
