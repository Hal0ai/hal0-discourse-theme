#!/usr/bin/env python3
"""
Push this theme's colour schemes into a Discourse instance.

Why this exists
----------------
FALLBACK, not a required step, since this repo graduated from a theme
component to a full theme (about.json's `component: false`). A full theme's
`color_schemes` install natively on a fresh git-repo install — Discourse
only skips that for components. From core's `app/models/remote_theme.rb`:

    update_theme_color_schemes(theme, theme_info["color_schemes"]) unless theme.component

Back when this repo *was* a component (component: true, pre-graduation),
that line meant `about.json`'s schemes were silently ignored and this script
was the only way to get them into Discourse at all. As a theme, a fresh
install doesn't need this script for that. What it's still useful for:
re-pushing `about.json`'s current colours through the admin API without a
full reinstall, any time those hex values change after the theme is already
installed and running (Discourse doesn't re-read about.json's colours on a
routine "check for updates" sync — see the README's Install section).

This also means the palette can drift into the site database independently
of git if someone edits a colour scheme by hand in Admin → Appearance. This
script pushes `about.json` at the instance and overwrites that drift; re-run
it whenever about.json's colours change and you don't want to reinstall.

Usage
-----
On the forum host, where the API key already lives:

    sudo python3 scripts/push-color-schemes.py

Or from anywhere, with credentials in the environment:

    DISCOURSE_URL=https://forum.hal0.dev \
    DISCOURSE_API_KEY=... DISCOURSE_API_USERNAME=system \
    python3 scripts/push-color-schemes.py

Options:
    --env-file PATH   read credentials from PATH
                      (default /srv/secrets/discourse-api.env if it exists)
    --theme-id ID     theme whose palette slots get pointed at the new
                      schemes (default: the site's default theme)
    --light NAME      scheme for the light slot (default "hal0 light")
    --dark NAME       scheme for the dark slot (default "hal0 dark")
    --dry-run         report what would change, write nothing

Why the light slot defaults to the light palette rather than forcing dark
everywhere: Discourse picks between the two slots with
`(prefers-color-scheme: light)`, and `scss/_hal0-tokens.scss` keys its own
light token overrides off the exact same media query. Point both slots at
"hal0 dark" and a visitor whose OS prefers light gets Discourse's dark
palette underneath the chrome's light tokens — a guaranteed mismatch. Keep
the slots honest and the two layers always agree.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = Path("/srv/secrets/discourse-api.env")


def load_credentials(env_file):
    values = dict(os.environ)
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                values.setdefault(key, value)
    missing = [k for k in ("DISCOURSE_URL", "DISCOURSE_API_KEY") if not values.get(k)]
    if missing:
        sys.exit(f"missing credentials: {', '.join(missing)} (see --help)")
    return values


class Discourse:
    def __init__(self, creds, dry_run=False):
        self.base = creds["DISCOURSE_URL"].rstrip("/")
        self.dry_run = dry_run
        self.headers = {
            "Api-Key": creds["DISCOURSE_API_KEY"],
            "Api-Username": creds.get("DISCOURSE_API_USERNAME", "system"),
            "Accept": "application/json",
        }

    def __call__(self, method, path, payload=None):
        if self.dry_run and method != "GET":
            print(f"    [dry-run] {method} {path}")
            return {}
        headers = dict(self.headers)
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base + path, data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            sys.exit(f"{method} {path} -> HTTP {exc.code}\n{exc.read().decode()[:400]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--theme-id", type=int)
    parser.add_argument("--light", default="hal0 light")
    parser.add_argument("--dark", default="hal0 dark")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    about = json.loads((REPO_ROOT / "about.json").read_text())
    schemes = about.get("color_schemes") or {}
    if not schemes:
        sys.exit("about.json declares no color_schemes")

    api = Discourse(load_credentials(args.env_file), dry_run=args.dry_run)

    existing = {s["name"]: s for s in api("GET", "/admin/color_schemes.json")}
    scheme_ids = {}

    for name, colors in schemes.items():
        payload = {
            "color_scheme": {
                "name": name,
                "colors": [{"name": k, "hex": v} for k, v in colors.items()],
            }
        }
        current = existing.get(name)
        if current:
            api("PUT", f"/admin/color_schemes/{current['id']}.json", payload)
            scheme_ids[name] = current["id"]
            print(f"  updated  {name} ({len(colors)} colors, id {current['id']})")
        else:
            created = api("POST", "/admin/color_schemes.json", payload)
            scheme_ids[name] = created.get("id")
            print(f"  created  {name} ({len(colors)} colors, id {scheme_ids[name]})")

    # Point a theme's palette slots at the schemes. A component cannot carry
    # a palette itself, so this targets the *base* theme the component is
    # attached to — by default whichever theme the site marks as default.
    theme_id = args.theme_id
    if theme_id is None:
        themes = api("GET", "/admin/themes.json").get("themes", [])
        default_theme = next((t for t in themes if t.get("default")), None)
        if not default_theme:
            sys.exit("no default theme found; pass --theme-id explicitly")
        theme_id = default_theme["id"]
        print(f"  target theme: {default_theme['name']} (id {theme_id})")

    for slot, wanted in (("color_scheme_id", args.light), ("dark_color_scheme_id", args.dark)):
        if wanted not in scheme_ids:
            sys.exit(f"scheme {wanted!r} is not declared in about.json")

    api("PUT", f"/admin/themes/{theme_id}.json", {
        "theme": {
            "color_scheme_id": scheme_ids[args.light],
            "dark_color_scheme_id": scheme_ids[args.dark],
        }
    })
    print(f"  theme {theme_id}: light slot -> {args.light!r}, dark slot -> {args.dark!r}")
    if args.light == args.dark:
        print("  WARNING: both slots point at the same scheme. Discourse will serve it to "
              "everyone, but scss/_hal0-tokens.scss still swaps its own tokens on "
              "(prefers-color-scheme: light) — so half the surface will disagree for "
              "visitors whose OS prefers the other mode.")


if __name__ == "__main__":
    main()
