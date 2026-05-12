# Bundled fonts

These are the default fonts used by `compose_page.py`. They are bundled so that lettering output is identical across machines (laptop, mac mini, CI). Both are licensed under the SIL Open Font License 1.1 — free for commercial use, redistribution allowed.

| Font | Use | License | Source |
|---|---|---|---|
| `ComicNeue-Bold.ttf` | dialogue, captions | SIL OFL 1.1 — see `OFL-ComicNeue.txt` | Craig Rozynski's [comicneue](https://github.com/crozynski/comicneue) repo |
| `Bangers-Regular.ttf` | SFX | SIL OFL 1.1 — see `OFL-Bangers.txt` | Vernon Adams via [Google Fonts](https://fonts.google.com/specimen/Bangers) |

`compose_page.py` resolves fonts in this order:

1. Env vars: `COMIC_FONT_DIALOG`, `COMIC_FONT_SFX`, `COMIC_FONT_CAPTION`
2. These bundled files
3. macOS system fonts (Comic Sans MS Bold, Impact, Arial Bold)
4. Pillow default font (last resort)

To swap in a different font for one project, set the env var when running the script. To swap permanently, replace the file in this directory (and update the license accordingly).

## License compliance

If you redistribute output that includes glyphs from these fonts (e.g. publishing the comic), you do **not** need to include the OFL text alongside the published comic. The OFL only requires attribution if you redistribute the font *files themselves*. Since the bundled `.ttf` files only travel inside this repo, the OFL files in this folder are sufficient.

If you fork this repo and redistribute, keep the OFL files alongside the fonts.
