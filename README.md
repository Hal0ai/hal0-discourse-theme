# hal0-discourse-theme

A Discourse **theme component** (not a full theme — installs alongside
whatever base theme `forum.hal0.dev` runs) that carries the hal0 brand into
Discourse: dark/light color schemes built from hal0's design tokens, and two
injected chrome pieces (a brand/nav strip above the topic list, a shared
footer below Discourse's own footer) so the forum reads as part of hal0.dev
rather than a bolted-on subdomain.

Design source: `hal0-web/docs/design/2026-08-09-community-comps/`
(`README.md` "The unified chrome" + screen 7 "Forum", `07 Forum.html`,
`hal0-site.css`). Brand tokens and nav links are **synced in**, never
hand-forked — see [Syncing from hal0-web](#syncing-from-hal0-web).

## What's in the box

```
about.json                                    theme metadata + hal0 dark/light color schemes
settings.yml                                  hal0_web_origin, show_hal0_chrome
common/
  common.scss                                 entry point: token import, Discourse var bridge,
                                               .hal0-chrome scoped CSS (ported from hal0-site.css)
scss/
  _hal0-tokens.scss                           AUTO-GENERATED — brand tokens as CSS custom properties.
                                               Must live here, not in common/: Discourse compiles
                                               common/common.scss as an entrypoint and only resolves
                                               @import partials out of scss/.
javascripts/discourse/
  connectors/
    above-main-container/hal0-header.gjs      brand + nav strip (active connector)
    below-footer/hal0-footer.gjs              shared footer (active connector)
  lib/
    hal0-nav-data.js                          AUTO-GENERATED — nav links from nav.json
    hal0-wordmark.js                          inline hal0 wordmark SVG (hand-copied, rarely changes)
    hal0-icons.js                             github/discord/rss glyph paths (hand-copied)
connectors-classic/                           reference-only classic Handlebars connectors (NOT loaded)
  above-main-container/hal0-header.hbs
  below-footer/hal0-footer.hbs
scripts/
  sync-from-hal0-web.mjs                      regenerates the two AUTO-GENERATED files above
  push-color-schemes.py                       installs about.json's colour schemes through the
                                               admin API (components can't ship them natively)
LICENSE                                       Apache-2.0, matching the hal0 project
```

## Install

Discourse admin → **Customize → Themes → Install → From a git repository**:

```
https://github.com/Hal0ai/hal0-discourse-theme
```

Install it as a **component**, then add it to whatever theme is active on
`forum.hal0.dev` (Themes → your active theme → Components → add "hal0 forum
theme").

Then push the colour schemes — **this step is not optional and is not done
for you**:

```bash
python3 scripts/push-color-schemes.py          # add --dry-run first to preview
```

Discourse **ignores `color_schemes` declared by a theme component**. Core's
`app/models/remote_theme.rb` guards the import with:

```ruby
update_theme_color_schemes(theme, theme_info["color_schemes"]) unless theme.component
```

So installing this component gets you the chrome and the `--hal0-*` tokens,
but leaves Discourse's own palette (topic rows, buttons, badges, links) on
whatever the base theme shipped — stock light, in practice. The script
creates "hal0 dark" and "hal0 light" from `about.json` through the admin API
and points the base theme's two palette slots at them, so `about.json` stays
the single source of truth and the palette does not quietly drift into the
site database. Re-run it whenever `about.json`'s colours change.

Credentials come from `/srv/secrets/discourse-api.env` on the forum host, or
from `DISCOURSE_URL` / `DISCOURSE_API_KEY` / `DISCOURSE_API_USERNAME` in the
environment. See `--help`.

Two theme settings (Customize → Themes → hal0 forum theme → Settings):

- `hal0_web_origin` — origin used to build absolute hrefs for the injected
  nav links (default `https://hal0.dev`). Only change this for a staging
  hal0-web deployment.
- `show_hal0_chrome` — master on/off switch for both connectors. Useful for
  isolating a style conflict without uninstalling the component.

## How the header actually attaches

Read this before comparing against `07 Forum.html` pixel-for-pixel: the
`above-main-container` plugin outlet renders **below** Discourse's own fixed
`.d-header`, not above it — there's no outlet above the native header itself.
So `hal0-header.gjs` does **not** replace or hide Discourse's header. Search,
notifications, the hamburger menu, and the user menu all stay **100% native
Discourse**, exactly as the design brief's "unified chrome" section requires
("composer/notifications/moderation/search/user cards stay native").

What this theme actually injects is a second, slimmer strip directly beneath
Discourse's native header: the hal0 wordmark, a `forum` host slug, and the
hal0.dev top nav (`learn` / `benchmarks` / `profiles`, each carrying the `↗`
cross-host marker). That strip carries the signature amber filament hairline
and reuses the same `.hdr` CSS as hal0.dev's own header. Discourse's native
header above it is restyled only via the color scheme (`about.json`) and the
small variable bridge in `common.scss` — it is not touched structurally.

If pixel-parity with the comp's single fused header (search/notifications/
avatar rendered inside the hal0-styled bar) turns out to be a hard
requirement after launch, that needs a different technique — most likely
CSS-hiding `.d-header`'s content and reimplementing its interactive pieces
inside the connector, wiring them to Discourse's `header` service / app
events. That's flagged as **open work**, not attempted here, because it
can't be built safely without a live Discourse instance to test against (see
[Validation](#validation-deferred-to-launch)).

## What is intentionally NOT themed here

Per the design brief's split of responsibility — restyled through
Discourse's own CSS variables / color scheme, not overridden with bespoke
markup:

- Topic list rows, badges, tags, unread pills, category colors
- Avatars, user cards, the user menu, notifications panel
- The composer, markdown editor, uploads
- Moderation tools, admin UI
- Discourse's own search (full-page search and the header search dropdown)
- Discourse's native header itself (see above) — only restyled, not replaced

Only the brand strip and footer are bespoke markup. Everything else stays
Discourse, colored to match.

## Connector format: .gjs (Glimmer), not classic Handlebars

Current Discourse (2025+) theme-component connectors are authored as
`.gjs` files under `javascripts/discourse/connectors/<outlet>/<name>.gjs` —
native Glimmer components with `<template>` syntax, replacing the older
plain-Handlebars `<outlet>/<name>.hbs` convention. That's what's active here.

Per the task brief, classic `.hbs` equivalents are also shipped, but only as
a **reference-only fallback** under `connectors-classic/` (not inside
`javascripts/discourse/`, so Discourse never loads them). They're
hard-coded — no `settings.yml` wiring, no sync script — because Discourse's
classic component connectors don't cleanly share a JS module with a Glimmer
one, and duplicating the real logic in two formats forever isn't worth it
for a fallback that current Discourse shouldn't need. If a launch-time
Discourse version genuinely can't compile the `.gjs` connectors, copy the
`.hbs` files into `javascripts/discourse/connectors/`, delete the `.gjs`
files, and hand-port the wordmark/icon markup from `hal0-wordmark.js` /
`hal0-icons.js`.

## Syncing from hal0-web

`scripts/sync-from-hal0-web.mjs` regenerates two files from a hal0-web
checkout so tokens and nav links are never hand-typed twice:

| Generated file | Source |
|---|---|
| `scss/_hal0-tokens.scss` | `src/styles/tokens.css` (`:root` + `[data-theme='light']` blocks) |
| `javascripts/discourse/lib/hal0-nav-data.js` | `src/data/nav.json` (`header`, `footerColumns`, `social`, `footerBase`) |

```bash
# explicit path
node scripts/sync-from-hal0-web.mjs /path/to/hal0-web

# or via env var
HAL0_WEB_DIR=/mnt/mintdev/repos/hal0-web node scripts/sync-from-hal0-web.mjs

# or rely on the default: ../hal0-web relative to this repo
node scripts/sync-from-hal0-web.mjs
```

Both generated files start with an `AUTO-GENERATED` banner — don't hand-edit
them; edit `hal0-web`'s source files and re-run the script instead. Run it
and commit the diff whenever hal0-web's tokens or nav change.

**Not covered by the sync script** (change these by hand if they drift):

- `about.json`'s `color_schemes` — Discourse's own scheme format
  (`primary`/`secondary`/`tertiary`/...) doesn't map 1:1 onto `--hal0-*`
  token names, so those hex values are hand-transcribed from `tokens.css`,
  **except** the light scheme's `danger`/`success` (`cf222e`/`1a7f37`).
  `tokens.css` doesn't carry light-mode `--err`/`--ok` overrides yet — those
  two values come from the design handoff doc instead
  (`hal0-web/docs/design/2026-08-09-community-comps/README.md`, "Colour —
  light overrides": `--ok #1a7f37 · --err #cf222e`, required for AA contrast
  on white). This is tracked on the hal0-web side; once tokens.css gains
  light `--err`/`--ok`, the sync script can be extended to cover them too.
  If hal0's palette changes elsewhere, update `about.json` by hand.
- `javascripts/discourse/lib/hal0-wordmark.js` and `hal0-icons.js` — the
  wordmark and github/discord/rss glyphs, copied once from
  `public/brand/logo-halo-dark.svg` and `site-chrome.jsx`'s `BrandIcon`.
  These change rarely enough that a sync step wasn't worth building.
- The footer base line's version string (`FOOTER_VERSION` in
  `hal0-footer.gjs`, currently `"1.0.0-rc.3"`) — mirrors
  `SiteFooter.astro`'s `footerVersion`, which comes from `parseChangelog()`
  over `hal0-web/src/data/changelog.md`'s latest `## [x.y.z]` entry. It is
  **not** `BINARY` from `model-roster.ts` or the homepage hero pill — those
  are a different version axis (the hal0 binary release, not the docs-site
  changelog the real footer actually reads). There's no automated source for
  changelog.md parsing in this repo yet; bump `FOOTER_VERSION` (and the
  matching hardcoded line in `connectors-classic/below-footer/hal0-footer.hbs`)
  by hand whenever hal0-web's changelog gains a new latest entry, or wire a
  future sync step to `changelog.js`'s `parseChangelog()` if that drifts
  often enough to be annoying.

## Validation

Installed and exercised against the live `forum.hal0.dev` (Discourse 8.0.5.1)
as a component of the Foundation base theme.

Done:

- [x] Installed via the git-repo installer. Needed three fixes first — the
      stylesheet did not compile (partial in the wrong directory) and both
      connectors threw on every render (methods invoked as template helpers
      lose `this`). See the commit history.
- [x] Colour schemes: found that components cannot ship them at all, and
      added `scripts/push-color-schemes.py` to close the gap. See
      [Install](#install).
- [x] `html.light-scheme` — **confirmed wrong**. Those are classes on the
      `<link>` elements for the two colour-scheme stylesheets, not on
      `<html>`; Discourse switches palettes with
      `(prefers-color-scheme: light)`
      (`application_helper.rb#light_elements_media_query`). The generated
      token file now uses that media query.
- [x] Wordmark — was rendering as a 19×19 speck because the inlined SVG kept
      the brand file's 1500×1500 square canvas. Cropped to the lettering's
      own band, matching hal0-web's `Wordmark.astro`.
- [x] Zero console errors on the categories index; brand strip renders once
      with all three nav links resolving against `hal0_web_origin`, footer
      renders with all three columns and its social row.

Still open:

- [ ] Screenshot the topic list and an open topic and compare against
      `07 Forum.html`'s `TopicList` / `TopicView` states. Only the categories
      index has been compared so far. The topic rows/badges/avatars are
      Discourse's own components restyled by the colour scheme — they are not
      exempt from the comparison just because this repo didn't write them.
- [ ] Confirm the brand strip's sticky/backdrop-blur behavior doesn't fight
      with Discourse's own sticky header (two stacked `position: sticky`
      elements can behave oddly depending on Discourse's header height and
      scroll-shrink behavior on mobile).
- [ ] Decide whether the brand-strip-below-native-header approach (see
      [How the header actually attaches](#how-the-header-actually-attaches))
      is acceptable, or whether full header replacement is required — and if
      so, scope that as separate follow-up work.
- [ ] Verify the footer's hardcoded `FOOTER_VERSION` against
      `hal0-web/src/data/changelog.md`'s actual latest entry at launch time.
- [ ] Check the `⌘K` / `/` search keyboard shortcut and Discourse's own
      search still work unobstructed with the extra strip in the DOM.
- [ ] Mobile: confirm the brand strip's nav links don't create a confusing
      double-hamburger situation next to Discourse's own mobile header
      controls.
- [ ] Manual light/dark toggle (`interface_color_selector`) is **not
      supported** — the chrome's tokens follow the OS preference, not the
      user's override, so the two layers would disagree. Bridging the chrome
      to Discourse's own `--primary`/`--secondary` variables would fix this
      properly and is the right shape for that work.

## License

Apache-2.0, matching the hal0 project.
