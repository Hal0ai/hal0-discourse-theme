#!/usr/bin/env python
"""Screenshot forum.hal0.dev surfaces in both schemes / widths.

usage: shot.py <tag> <path> [--w 1440] [--h 1400] [--full] [--scheme dark|light|both]
"""
import sys, os, time, json
from playwright.sync_api import sync_playwright

BASE = "https://forum.hal0.dev"
OUT = "/tmp/hal0shots"


def creds():
    env = {}
    p = os.path.join(OUT, ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v
    return env



def load_css(path):
    """Read a theme SCSS partial as injectable CSS.

    The partials use `//` line comments, which are valid SCSS but garbage to a
    CSS parser -- it resyncs by swallowing whole rules, so an un-stripped file
    silently applies about half of itself. Only full-line comments are removed;
    `https://` inside a value is left alone.
    """
    out = []
    for line in open(path):
        if line.lstrip().startswith("//"):
            continue
        out.append(line)
    return "".join(out)


def run(tag, path, w=1440, h=1400, full=False, schemes=("dark", "light"), clip_sel=None,
        wait=2500, auth=False, css=None):
    files = []
    hdr = {}
    if auth:
        e = creds()
        hdr = {"Api-Key": e["DISCOURSE_API_KEY"],
               "Api-Username": e["DISCOURSE_API_USERNAME"]}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/chromium",
                              args=["--no-sandbox", "--disable-gpu"])
        for scheme in schemes:
            ctx = b.new_context(viewport={"width": w, "height": h},
                                color_scheme=scheme,
                                device_scale_factor=1,
                                is_mobile=(w < 500),
                                has_touch=(w < 500))
            if hdr:
                # Only authenticate navigations and data calls — signing every
                # static asset burns the API key's rate limit in one page load.
                def _auth(route):
                    if route.request.resource_type in ("document", "xhr", "fetch"):
                        route.continue_(headers={**route.request.headers, **hdr})
                    else:
                        route.continue_()
                ctx.route("**/*", _auth)
            pg = ctx.new_page()
            pg.goto(BASE + path, wait_until="load", timeout=60000)
            pg.wait_for_timeout(wait)
            try:
                pg.wait_for_selector(".topic-list, .category-list, .topic-post, .container", timeout=8000)
            except Exception:
                pass
            pg.wait_for_timeout(800)
            for c in css or []:
                pg.evaluate("""(css)=>{const s=document.createElement('style');s.setAttribute('data-hal0-preview','');s.textContent=css;document.body.appendChild(s);}""", load_css(c))
            if css:
                pg.wait_for_timeout(400)
            f = f"{OUT}/{tag}-{scheme}-{w}.png"
            if clip_sel:
                el = pg.query_selector(clip_sel)
                if el:
                    el.screenshot(path=f)
                else:
                    pg.screenshot(path=f, full_page=full)
            else:
                pg.screenshot(path=f, full_page=full)
            files.append(f)
            ctx.close()
        b.close()
    print("\n".join(files))


if __name__ == "__main__":
    a = sys.argv[1:]
    tag, path = a[0], a[1]
    kw = {}
    if "--w" in a:
        kw["w"] = int(a[a.index("--w") + 1])
    if "--h" in a:
        kw["h"] = int(a[a.index("--h") + 1])
    if "--full" in a:
        kw["full"] = True
    if "--scheme" in a:
        s = a[a.index("--scheme") + 1]
        kw["schemes"] = (s,) if s != "both" else ("dark", "light")
    if "--clip" in a:
        kw["clip_sel"] = a[a.index("--clip") + 1]
    if "--auth" in a:
        kw["auth"] = True
    if "--css" in a:
        kw["css"] = [x for x in a[a.index("--css") + 1:] if not x.startswith("--")]
    if "--wait" in a:
        kw["wait"] = int(a[a.index("--wait") + 1])
    run(tag, path, **kw)
