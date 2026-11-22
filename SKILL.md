---
name: scribus-sla
description: Create, fill, edit and export Scribus .sla files with the real Scribus engine so the output matches the desktop app (PDF, fillable PDF, PDF/X, PNG/JPG, SVG, EPS, PS). Use for any .sla or Scribus task.
---

# Scribus .sla files, done with real Scribus

Never hand-render or approximate a Scribus document, and never write a whole `.sla` by hand.
This skill installs the real Scribus (default 1.6.3) and a small `sla` command around it.
Exports made this way were checked against PDFs exported from the Scribus 1.6.3 desktop
app: 11 documents (plain, with images, and fillable forms) matched pixel for pixel.

## 1. Install (once per session, 2-4 minutes the first time)

```bash
[ -d /opt/sla/kit/.git ] || git clone --depth 1 https://github.com/JessNco/scribus-sla /opt/sla/kit
bash /opt/sla/kit/scripts/setup.sh
```

- Another Scribus version: `bash /opt/sla/kit/scripts/setup.sh 1.6.5` (also `1.6.1`, `native`).
  Match the version the user runs; a file saved by the engine carries the engine's version.
- Needs root, `apt`, and network access to `github.com` and `archive.ubuntu.com`. Finishes with a
  line starting `[sla-setup] ready:`. If it warns that it fell back to another version, tell the user.
- The engine can only see files under `/home`, `/tmp`, `/mnt`, `/root`. Work there.

## 2. Commands

```bash
sla inspect FILE.sla -v            # pages, fonts (installed?), images (found?), named items, {{placeholders}}, form fields
sla export FILE.sla                # PDF next to the .sla, using the document's own saved PDF settings
sla export FILE.sla -f pdf,png,svg,eps,ps,jpg --dpi 300 -d OUTDIR --pages 1,3-5
sla export FILE.sla --pdf-version x4 --crop-marks --bleed 8.5      # print PDF (x1a, x3, x4; --cmyk; --profile)
sla fill TEMPLATE.sla OUT.sla --set name=Value --text frame_name="New text" --image frame_name=new.png
sla resave IN.sla OUT.sla          # open in Scribus and save: proves the file loads, normalises it
sla run SCRIPT.py [args]           # run a Scribus Python (scripter) script; this is how new documents are made
sla compare A.pdf B.pdf --out DIR  # pixel comparison, same renderer and DPI for both; writes diff images
sla fonts --grep sans              # exact font names as Scribus spells them
sla fonts --add FILE_OR_DIR        # install the user's font files
sla fonts --google "Comic Relief"  # open-licensed families from Google Fonts
```

`sla <command> -h` lists every option.

## 3. Rules that keep the output identical to the desktop app

1. **Missing fonts or images stop the export.** Scribus substitutes a missing font silently and
   the layout shifts. `sla export` refuses and names what is missing. Install the font
   (`sla fonts --add/--google`) or fix the image path. Only pass `--allow-missing` if the user accepts it.
   Font names must match exactly, e.g. `Latin Modern Sans 10 Bold`, `DejaVu Sans Book`.
2. **Image links are relative to the `.sla` file.** Keep a document and its assets in the same
   relative layout as on the user's computer, or the frames export empty.
3. **Export uses the document's saved PDF settings** (compression, PDF version, fonts). Override
   only on request: `--lossless`, `--outline-fonts`, `--pdf-version`, `--pdf-option KEY=VALUE`.
4. **Fillable PDFs just work.** For documents with form fields the tool embeds the field font in
   full, as the desktop export dialog does. (Plain scripted export crashes on these; do not work
   around it with outlined fonts.)
5. **Look at the result.** After any create/fill/edit: `sla export FILE.sla -f png --dpi 72 -d /tmp/preview`
   and view the PNG. When a reference PDF exists, run `sla compare` and expect `MATCH` at 0.0000%.
6. **Format notes.** PNG/JPG come from Scribus's own "Save as Image" (use `--raster-via pdf` to
   rasterise the PDF instead; sizes can differ by one pixel). SVG and PS are converted from the
   exported PDF (text becomes outlines in SVG). EPS is Scribus's own, one file per page.

## 4. Filling a template

- Put `{{name}}` in the template text; `--set name=value` replaces it everywhere. A placeholder
  must sit in one formatting run (type it in one go, same font and size throughout).
- `--text ITEM=value` replaces the whole text of the frame named ITEM, keeping its first run's
  formatting; `\n` starts a new paragraph. Names are the item names shown by `sla inspect -v`
  (Scribus: Properties > Name).
- `--image ITEM_OR_OLD_FILENAME=new.png` relinks a picture and fits it to its frame. Add
  `--keep-image-scale` to keep the old scale instead.
- `--data file.json` takes `{"placeholders": {}, "text": {}, "images": {}}`. `--strict` fails if a key matched nothing.
- The result is re-saved by Scribus, so it is a genuine Scribus file.

## 5. Creating a new document

Write a scripter script and run it with `sla run`. A complete, tested example is installed at
`/opt/sla/kit/examples/new_document.py` (page setup, colours, styles, text, shapes, lines, image,
save). Copy it and adapt. Essentials:

- Wrap the script in `try: ... finally: os._exit(0)` or Scribus never quits.
- Define colours and styles first; name every object (`createText(x, y, w, h, "name")`).
- `\r` separates paragraphs in `setText`. Units are whatever `newDocument` was given (use points).
- `setScaleImageToFrame(True, True, name)` fits a picture to its frame, keeping proportions.
- Save with `saveDocAs(path)`, then `sla inspect` and preview it (rule 5).
- To match an existing house style, `sla inspect -v` one of the user's documents first and reuse
  its page size, fonts, colours and line weights.

## 6. Editing an existing document

Prefer a scripter script (`openDoc`, change objects by name, `saveDocAs`). Small attribute edits
in the XML are fine; run `sla resave` afterwards and preview. Useful XML facts (Scribus 1.6):

- Root `SCRIBUSUTF8NEW`, one `DOCUMENT`. Objects are `PAGEOBJECT` (pages), `MASTEROBJECT`
  (master pages), `FRAMEOBJECT` (inline). `PTYPE`: 2 image, 4 text, 5 line, 6 shape, 7 polyline, 12 group.
- Pages are stacked on one canvas: an object's `XPOS`/`YPOS` include its page's `PAGEXPOS`/`PAGEYPOS`.
- Text lives in `StoryText`: `ITEXT CH="..."` runs, `para`, `trail`. Fonts are `FONT="..."` attributes.
- Images: `PFILE` (path relative to the .sla). `SCALETYPE="0"` fit to frame (Scribus recomputes the
  scale on load), `SCALETYPE="1"` free scaling using `LOCALSCX/LOCALSCY/LOCALX/LOCALY`;
  `RATIO="1"` keeps proportions.
- A text frame's `path`/`copath` hold its shape: change them together with `WIDTH`/`HEIGHT`
  (or resize in a scripter script with `sizeObject`, which does it for you).
- Form fields: a text frame with `ANNOTATION="1"`, `ANTYPE` 3 text, 4 check box, 5 combo, 6 list.
- Do not save over the user's original; write a new file unless asked.

## 7. If something fails

- "Scribus exited ... crashed": run `sla inspect`, fix missing fonts/images, try `sla resave` to see
  whether the file loads at all, then export page by page (`--pages N`) to find the object.
- Engine build failed: `bash /opt/sla/kit/scripts/setup.sh native` installs the distribution's
  Scribus instead (exports matched the references too in testing; saved files carry that version).
- Fonts the user's document needs that are not open-licensed (e.g. Arial, Calibri): ask the user
  for the font files.
