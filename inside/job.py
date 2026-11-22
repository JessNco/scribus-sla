# Runs INSIDE Scribus (scribus -py job.py JOB.json). Do not run with plain python.
# Executes one job: open a document, optionally save it, and export it.
import json, os, sys, traceback
import scribus

def page_list(spec, n):
    if not spec:
        return list(range(1, n + 1))
    if isinstance(spec, list):
        return [p for p in spec if 1 <= p <= n]
    out = []
    for part in str(spec).split(","):
        a, _, b = part.strip().partition("-")
        out += range(int(a), int(b or a) + 1)
    return [p for p in out if 1 <= p <= n]

def annotation_fonts(job, res):
    """Fonts used by PDF form fields. The desktop export dialog always embeds these in full
    (never subsets them); the scripter does not, and Scribus then crashes. Mirror the dialog."""
    fonts = set()
    by_master = {}
    for it in job.get("annotation_items", []):
        by_master.setdefault(it.get("master", ""), []).append(it["name"])
    for master, names in by_master.items():
        if master:
            try:
                scribus.editMasterPage(master)
            except Exception:
                continue
        for name in names:
            try:
                fonts.add(scribus.getFont(name))
            except Exception as e:
                res["warnings"].append("form field %s: %s" % (name, e))
        if master:
            scribus.closeMasterPage()
    return fonts

def main(job):
    res = {"ok": False, "outputs": [], "warnings": []}
    try:
        if not scribus.openDoc(job["input"]):
            raise RuntimeError("Scribus could not open " + job["input"])
        n = scribus.pageCount()
        res["pages"] = n
        if job.get("probe_form_fonts"):
            res["form_fonts"] = sorted(annotation_fonts(job, res))
        res["scribus"] = scribus.SCRIBUS_VERSION if hasattr(scribus, "SCRIBUS_VERSION") else ""
        for out in job.get("outputs", []):
            kind = out["type"]
            pages = page_list(out.get("pages"), n)
            if kind == "pdf":
                pdf = scribus.PDFfile()      # starts from the document's own saved PDF settings
                afonts = annotation_fonts(job, res)
                if afonts:
                    pdf.subsetList = [f for f in pdf.subsetList if f not in afonts]
                    pdf.fonts = sorted(set(pdf.fonts) | afonts)
                    res["form_fonts"] = sorted(afonts)
                for k, v in out.get("options", {}).items():
                    if not hasattr(pdf, k):
                        raise RuntimeError("unknown PDF option: " + k)
                    setattr(pdf, k, v)
                if out.get("pages"):
                    pdf.pages = pages
                pdf.file = out["file"]
                pdf.save()
                res["outputs"].append(out["file"])
            elif kind in ("png", "jpg", "tiff", "bmp"):
                img = scribus.ImageExport()
                img.type = {"jpg": "JPG", "png": "PNG", "tiff": "TIFF", "bmp": "BMP"}[kind]
                img.dpi = int(out.get("dpi", 300))
                img.scale = int(out.get("scale", 100))
                img.quality = int(out.get("quality", 95))
                if kind == "png":
                    img.transparentBkgnd = bool(out.get("transparent", False))
                for p in pages:
                    scribus.gotoPage(p)
                    f = out["pattern"] % p
                    img.saveAs(f)
                    res["outputs"].append(f)
            elif kind == "eps":
                for p in pages:
                    scribus.gotoPage(p)
                    f = out["pattern"] % p
                    scribus.savePageAsEPS(f)
                    res["outputs"].append(f)
            elif kind == "sla":
                scribus.saveDocAs(out["file"])
                res["outputs"].append(out["file"])
            else:
                raise RuntimeError("unknown output type " + kind)
        scribus.closeDoc()
        res["ok"] = True
    except BaseException as e:
        res["error"] = "%s: %s" % (type(e).__name__, e)
        res["trace"] = traceback.format_exc()
    with open(job["result"], "w") as fh:
        json.dump(res, fh)

try:
    with open(sys.argv[1]) as fh:
        main(json.load(fh))
finally:
    sys.stdout.flush()
    os._exit(0)   # never leave a Scribus process behind
