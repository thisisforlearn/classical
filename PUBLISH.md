# 🚢 Publish guide — get `symphonix` on PyPI in 5 minutes

The GitHub repo is already live: https://github.com/thisisforlearn/classical
The workflow files are already committed. You only do the one-time PyPI setup.

---

## EASIEST WAY (recommended): GitHub Actions auto-publish

The repo already has `.github/workflows/publish.yml` — every time you push a tag
like `v1.0.1`, GitHub builds and publishes to PyPI for you. **No tokens needed.**

### One-time setup (5 min):

1. Create a free account at **https://pypi.org** (log in with GitHub is easiest).
2. Go to **https://pypi.org/manage/account/publishing/**
3. Fill the form:
   - PyPI project name: `symphonix`  *(verified free — nobody owns it)*
   - Owner: `thisisforlearn`
   - Repository: `classical`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
4. Submit. That's the whole setup.

### Then every release is just:

```bash
cd ~/pylib-making
# bump version in pyproject.toml first, e.g. version = "1.0.1"
git add -A && git commit -m "release 1.0.1"
git tag v1.0.1 && git push origin main --tags
```

GitHub Actions builds the sdist + wheel and publishes.
Your package appears at **https://pypi.org/project/symphonix/** within a minute.

### Anyone on earth installs it with:

```bash
pip install symphonix
sx play bach
```

---

## Manual fallback (if you don't want Actions):

```bash
# on your machine (you'll need internet + your PyPI token):
pip install build twine
cd ~/pylib-making
python -m build
twine upload dist/*
# when asked for credentials: username=__token__ password=pypi-XXXX(ppi token)
```

Get the token at https://pypi.org/manage/account/token/ (API token → scope: project `symphonix`).

> I already produced a wheel here (dist/symphonix-1.0.0-py3-none-any.whl),
> but building on GitHub first-upload is safer because PyPI reads the license
> file and README straight from the build CI context.

---

## After first upload — make it shine (recommended, optional):

1. On GitHub repo → Settings → Branches → protect `main` (optional)
2. Open a GitHub **Discussion** or at least add topics:
   `music`, `classical`, `cli`, `tui`, `public-domain`, `player`
3. Mention it in a post with a terminal GIF — `svg-term` or `terminalizer` captures
   `sx play chopin nocturne` beautifully (equalizer + animations look great on video).
4. Add a short "demo" to the README later; the README already explains everything.

## everyday updates flow (once published):

```bash
# edit something
bump version in pyproject.toml (1.0.1 → 1.0.2)
git add -A; git commit -m "new feature"; git push
git tag v1.0.2; git push --tags      # → auto-published
```

## Updating code later (already pushed to GitHub):

```bash
cd ~/pylib-making                    # your local clone
git pull                             # first time: git clone https://github.com/thisisforlearn/classical
# edit files...
git add -A && git commit -m "describe change" && git push
```
