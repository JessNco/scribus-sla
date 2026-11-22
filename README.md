# scribus-sla

Work with [Scribus](https://www.scribus.net/) `.sla` files from a script or an AI assistant, using the
real Scribus engine, so exports match what the desktop app produces.

- **Export** to PDF (including fillable forms), PDF/X, PNG, JPG, SVG, EPS and PostScript
- **Fill** templates: `{{placeholders}}`, named text frames, images
- **Create** new documents with Scribus's own Python scripter
- **Inspect** a document: fonts, images, named items, form fields, and what is missing
- **Compare** two PDFs pixel by pixel

It runs headless on Debian/Ubuntu (tested on Ubuntu 24.04, as root, in a container).

## Install

```bash
git clone --depth 1 https://github.com/JessNco/scribus-sla /opt/sla/kit
bash /opt/sla/kit/scripts/setup.sh          # Scribus 1.6.3; or pass 1.6.5, 1.6.1 or native
```

Setup builds a small Ubuntu root under `/opt` that holds the chosen Scribus version (2 to 4 minutes),
so the host's own libraries are left alone. `native` installs the host's `scribus` package instead.

## Use

```bash
sla inspect FILE.sla -v
sla export FILE.sla                                   # PDF next to the .sla
sla export FILE.sla -f pdf,png,svg,eps,ps --dpi 300 -d out/
sla export FILE.sla --pdf-version x4 --crop-marks --bleed 8.5
sla fill TEMPLATE.sla OUT.sla --set name=Value --text frame="New text" --image frame=new.png
sla run examples/new_document.py /tmp/new.sla         # build a document from scratch
sla compare A.pdf B.pdf --out diff/
sla fonts --add MyFont.ttf      # or: sla fonts --google "Comic Relief"
```

`sla <command> -h` lists every option. [`SKILL.md`](SKILL.md) is the full guide.

## Use it as a Claude skill

`SKILL.md` is written as a Claude skill: add it to Claude as a skill named `scribus-sla` and Claude
will install and use these tools whenever it works on a `.sla` file.

## How it was checked

Eleven PDFs exported from the Scribus 1.6.3 desktop app (plain pages, pages with images, and fillable
forms) were re-exported with `sla export` and compared at 200 dpi: every page was identical. The
fillable exports carry the same form fields and embedded fonts as the desktop files. PNG, SVG, EPS, PS
and PDF/X output works but was not compared against desktop-made files.

## Notes

- Export refuses to run when a font or linked image is missing, because Scribus would otherwise
  substitute the font silently and the layout would shift.
- Documents with PDF form fields: the tool embeds the field font in full, as the desktop export
  dialog does. Plain scripted export crashes on these.
- SVG and PS are converted from the exported PDF. PNG/JPG come from Scribus's own image export.
