#!/usr/bin/env python
"""Probe computed styles with local CSS injected, and report which rules match."""
import sys, json
from playwright.sync_api import sync_playwright
from shot import creds, BASE, load_css

JS = """
(sel) => {
  const e = document.querySelector(sel);
  if (!e) return {sel, missing: true};
  const c = getComputedStyle(e), r = e.getBoundingClientRect();
  return {sel, cls: e.className, tag: e.tagName,
    w:+r.width.toFixed(1), h:+r.height.toFixed(1),
    font: c.fontFamily.split(',')[0]+' '+c.fontSize+'/'+c.fontWeight,
    color:c.color, bg:c.backgroundColor, border:c.border, radius:c.borderRadius,
    pad:c.padding, minh:c.minHeight, height:c.height, display:c.display};
}
"""


def main(path, css, sels, scheme="dark"):
    e = creds()
    hdr = {"Api-Key": e["DISCOURSE_API_KEY"], "Api-Username": e["DISCOURSE_API_USERNAME"]}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        ctx = b.new_context(viewport={"width": 1440, "height": 1400}, color_scheme=scheme)
        ctx.route("**/*", lambda r: r.continue_(headers={**r.request.headers, **hdr})
                  if r.request.resource_type in ("document", "xhr", "fetch") else r.continue_())
        pg = ctx.new_page()
        pg.goto(BASE + path, wait_until="load", timeout=60000)
        pg.wait_for_timeout(3500)
        for c in css:
            pg.evaluate("""(css)=>{const s=document.createElement('style');s.setAttribute('data-hal0-preview','');s.textContent=css;document.body.appendChild(s);}""", load_css(c))
        pg.wait_for_timeout(500)
        for s in sels:
            print(json.dumps(pg.evaluate(JS, s)))
        b.close()


if __name__ == "__main__":
    i = sys.argv.index("--sel")
    main(sys.argv[1], sys.argv[2:i], sys.argv[i + 1:])
