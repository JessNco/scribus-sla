# Example: build a new .sla from scratch with the Scribus scripter (run with: sla run new_document.py OUT.sla)
# Everything is created by Scribus itself, so the saved file is a genuine Scribus document.
import os, sys
import scribus as sc

out = os.path.abspath(sys.argv[1])
try:
    # A4 portrait, 40 pt margins, points as the unit, single pages
    sc.newDocument(sc.PAPER_A4, (40, 40, 40, 40), sc.PORTRAIT, 1, sc.UNIT_POINTS, sc.PAGE_1, 0, 1)
    W, H = sc.getPageSize()

    # colours (RGB) and styles first, then objects that use them
    sc.defineColorRGB("Ink", 74, 42, 26)
    sc.defineColorRGB("Paper", 234, 215, 173)
    sc.createCharStyle(name="Title", font="Latin Modern Mono 10 Regular", fontsize=20, fillcolor="Ink")
    sc.createParagraphStyle(name="Title", linespacingmode=1, alignment=sc.ALIGN_RIGHT, charstyle="Title")
    sc.createCharStyle(name="Body", font="Latin Modern Sans 10 Regular", fontsize=12, fillcolor="Ink")
    sc.createParagraphStyle(name="Body", linespacingmode=1, alignment=sc.ALIGN_LEFT, charstyle="Body")

    # header bar: rectangle + right-aligned title. Name every object you may want to find again.
    bar = sc.createRect(42, 42, W - 84, 34, "header_bar")
    sc.setFillColor("Paper", bar); sc.setLineColor("Ink", bar); sc.setLineWidth(2.83, bar)
    title = sc.createText(48, 46, W - 96, 28, "title")
    sc.setText("{{title}}", title)                 # a placeholder that `sla fill --set title=...` replaces
    sc.setParagraphStyle("Title", title)

    body = sc.createText(42, 100, W - 84, 120, "body")
    sc.setText("First paragraph.\rSecond paragraph.", body)   # \r separates paragraphs
    sc.selectText(0, sc.getTextLength(body), body)
    sc.setParagraphStyle("Body", body)

    # write-on lines
    for i in range(8):
        y = 260 + i * 25
        ln = sc.createLine(49, y, W - 49, y, "line_%d" % (i + 1))
        sc.setLineColor("Black", ln); sc.setLineWidth(1, ln)

    # an image frame: fit the image to the frame, keeping proportions
    if len(sys.argv) > 2:
        img = sc.createImage(W - 142, 100, 100, 100, "picture")
        sc.loadImage(os.path.abspath(sys.argv[2]), img)
        sc.setScaleImageToFrame(True, True, img)

    sc.saveDocAs(out)
finally:
    os._exit(0)      # always end a script this way so Scribus quits
