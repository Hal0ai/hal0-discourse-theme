# Theme preview harness

Renders the LIVE forum with a candidate SCSS partial injected, so styling can be
verified against real markup before a commit ever reaches the theme. Built and
used during the 2026-08-22 destock sweep; see repo issue #22 for the follow-ups
this exists to serve.

- `shot.py` — screenshots. `--scheme dark|light|both`, `--w 390`, `--full`,
  `--auth` for a signed-in view.
- `probe2.py` — computed-style probe (assert what the browser actually resolved,
  not what the stylesheet claims).

Setup: python venv with playwright + system chromium; credentials come from a
local copy of `/srv/secrets/discourse-api.env` on the forum host (`scp
hal0vps:/srv/secrets/discourse-api.env .env` — never commit it, shred after).

Two gotchas baked into the injector — do not "simplify" them away:

1. It strips `//` line comments from the partial before injecting. Valid SCSS,
   garbage to a CSS parser — un-stripped, roughly half a file silently fails to
   apply and everything looks mysteriously unstyled.
2. It appends the `<style>` at the END of `<body>`, because Discourse's
   interface-color toggle re-appends its own `<link>` elements and would
   otherwise win the cascade over the injected candidate.

`--auth` signs only `document`/`xhr`/`fetch` requests. Signing static assets
burns the API key's rate limit in a single page load.
