# hal0-discourse-theme

A Discourse **theme** (installed directly, not layered as a component onto
some other base theme) that carries the hal0 brand into Discourse: dark/light
color schemes built from hal0's design tokens, and chrome injected into
Discourse's own header and footer — the wordmark, the hal0 nav, a sub-nav,
and the shared site footer — so the forum reads as part of hal0.dev rather
than a bolted-on subdomain.

Was a theme *component* through rc.3 (see git history); graduated to a full
theme so `about.json`'s `color_schemes` install natively and the brand
tokens can be wired to Discourse's own light/dark toggle instead of the
visitor's OS preference — see [Install](#install) and
[Syncing from hal0-web](#syncing-from-hal0-web) for what that changed.

Design source: `hal0-web/docs/design/2026-08-09-community-comps/`
(`README.md` "The unified chrome" + screen 7 "Forum", `07 Forum.html`,
`hal0-site.css`). Brand tokens and nav links are **synced in**, never
hand-forked — see [Syncing from hal0-web](#syncing-from-hal0-web).

## What's in the box

```
about.json                                    theme metadata + hal0 dark/light color schemes +
                                               the only_theme_color_schemes modifier
settings.yml                                  hal0_web_origin, show_hal0_chrome
common/
  common.scss                                 entry point: token import, Discourse var bridge,
                                               .hal0-chrome scoped CSS (ported from hal0-site.css)
  color_definitions.scss                      AUTO-GENERATED — the --hal0-* tokens that differ
                                               between light/dark, compiled once per Discourse
                                               ColorScheme. Must live here, at exactly this path —
                                               see its header and "Syncing from hal0-web" below.
stylesheets/
  _hal0-discourse.scss                        Discourse-surface restyle: topic list, tags, category
                                               badges/page, nav pills, accepted answer, role chips,
                                               sidebar, welcome banner, header/banner search
  _hal0-docs.scss                             /docs (discourse-docs plugin) restyle: search field,
                                               category/tag filter sidebar, docs-topic-list as a
                                               .dtable, docs-topic back-link — plus the
                                               discourse-docs-card-filter component's cards as the
                                               KB category-card anatomy (icon, mono title, blurb,
                                               hover filament)
  _hal0-tokens.scss                           AUTO-GENERATED — the --hal0-* tokens that are
                                               identical in both schemes (fonts, radii, motion).
                                               Must live here, not in common/: Discourse compiles
                                               common/common.scss as an entrypoint and resolves
                                               @import partials out of stylesheets/.
javascripts/discourse/
  connectors/
    home-logo-contents/hal0-wordmark.gjs      inline wordmark, replacing the uploaded logo
    before-header-panel/hal0-nav.gjs          "forum" slug + hal0 nav, inline in Discourse's header
    after-header/hal0-subnav.gjs              the comp's second bar (latest · top · categories · …)
    below-footer/hal0-footer.gjs              shared footer
  lib/
    hal0-nav-data.js                          AUTO-GENERATED — nav links from nav.json
    hal0-wordmark.js                          inline hal0 wordmark SVG (hand-copied, rarely changes)
    hal0-icons.js                             github/discord/rss glyph paths (hand-copied)
connectors-classic/                           reference-only classic Handlebars connector (NOT loaded)
  below-footer/hal0-footer.hbs
scripts/
  sync-from-hal0-web.mjs                      regenerates the three AUTO-GENERATED files above
  push-color-schemes.py                       FALLBACK — re-syncs about.json's colour schemes
                                               through the admin API without a full reinstall (see
                                               Install below for why a component-era install needs
                                               a real reinstall, not this script, to pick up
                                               component: false)
  push-content-model.py                       tag groups, form templates and their category
                                               assignments — the forum's structured post types
LICENSE                                       Apache-2.0, matching the hal0 project
```

## Install

Discourse admin → **Customize → Themes → Install → From a git repository**:

```
https://github.com/Hal0ai/hal0-discourse-theme
```

Install it as a **theme** — leave "component" unchecked (it's the installer
default for a `component: false` about.json, but double-check: the installer
UI's checkbox reflects what it read from the repo, this isn't something you
choose independently). Then make it the site's active theme, or add it to
the theme selector as one of the choices, per how `forum.hal0.dev` wants to
run themes.

`about.json`'s `color_schemes` install **natively** now, no follow-up script
required for a fresh install. The `modifiers.only_theme_color_schemes: true`
flag (see `about.json`) tells Discourse's installer to auto-wire *both*
palette slots from the declared schemes on first install — light from
whichever scheme isn't dark, dark from whichever is — see
`app/models/remote_theme.rb`'s `only_theme_color_schemes` branch. Without
that flag a fresh install only wires the light slot and leaves dark to be
set by hand (Admin → Appearance → Themes → this theme → "Dark Color
Palette").

**If you're migrating this specific theme from its old component-era
install on `forum.hal0.dev`: merging this PR and letting Discourse "check
for updates" is *not* enough.** Read from `RemoteTheme.update_from_remote`:
the `component` attribute is only re-read from `about.json` on the code path
used for a *brand-new* theme record (`existing == false`, or the narrow
`!local_version` placeholder-sync branch right after creation) — a routine
remote-theme sync on an already-installed theme does not re-derive
`component` from the updated about.json at all. **Remove the existing
component from the active theme's Components list, then reinstall this repo
from scratch as a theme** (same git-repo install flow above) for
`component: false` to actually take effect. That reinstall also loses the
`hal0_web_origin` / `show_hal0_chrome` setting values and detaches it from
whatever theme it was a component of — note both down before removing the
old install.

`scripts/push-color-schemes.py` is now a **fallback**, not a required step:
use it if `about.json`'s colours change later and you'd rather re-push the
two schemes through the admin API than do a full reinstall. It still works
unchanged — themes accept `color_schemes` pushes the same way components do,
this was never a component-only limitation, only *installer-time* import
was.

Credentials come from `/srv/secrets/discourse-api.env` on the forum host, or
from `DISCOURSE_URL` / `DISCOURSE_API_KEY` / `DISCOURSE_API_USERNAME` in the
environment. See `--help`.

Two theme settings (Customize → Themes → hal0 forum theme → Settings):

- `hal0_web_origin` — origin used to build absolute hrefs for the injected
  nav links (default `https://hal0.dev`). Only change this for a staging
  hal0-web deployment.
- `show_hal0_chrome` — master on/off switch for both connectors. Useful for
  isolating a style conflict without uninstalling the theme.

## How the header actually attaches

There is **one** header: Discourse's own `.d-header`, restyled, with hal0
content injected into it. Two bars total, matching `07 Forum.html`, which
renders `<Header variant="forum" sticky />` followed by a `subnav`.

| Outlet | What goes in it |
|---|---|
| `home-logo-contents` | the inline wordmark (the uploaded `logo` is a 1500×1500 square artboard and cannot be cropped as an `<img>`) |
| `before-header-panel` | the `forum` slug and the hal0 nav — this outlet sits in `header/contents.gjs` between the home logo and the panel carrying search / notifications / the user menu, which is the comp's forum-variant order exactly |
| `after-header` | the sub-nav (`latest · top · categories · my posts · hal0.dev ↗`). It renders *inside* `<header>`, so the bar travels with the sticky header rather than creating a second sticky context |
| `below-footer` | the shared footer |

Discourse's search, notifications, hamburger and user menu are **100%
native** and structurally untouched, exactly as the design brief requires
("composer/notifications/moderation/search/user cards stay native"). They
are restyled only through the colour scheme and the variable bridge in
`common.scss`.

Two core rules have to be overridden for this to lay out correctly, and both
are load-bearing:

- `.d-header` is pinned to `3.66em`/`4em`. It needs `height: auto`, or the
  56px header row and the sub-nav overflow it — and because Discourse
  measures that element to publish `--header-offset`, the overflow is drawn
  on top of the page content.
- `.d-header` is a column flex container that does not stretch its children,
  so the sub-nav needs an explicit `width: 100%` or it shrink-wraps to its
  tabs and floats in the middle of the page.

An earlier version injected a whole second brand strip into
`above-main-container`. That outlet renders *below* the native header, so the
result was two stacked bars, the wordmark drawn twice, and a mostly empty
56px band. Everything it carried now lives in the real header.

## What is intentionally NOT themed here

Per the design brief's split of responsibility. Topic list rows, badges,
tags, unread pills, category colours and layout, the accepted-answer
treatment, the sidebar, the welcome banner, and header/welcome-banner search
ARE restyled — see `stylesheets/_hal0-discourse.scss`, which changes no
markup and only targets classes (or, for the sidebar, the `--d-sidebar-*`
custom properties) Discourse already renders/exposes. Left entirely alone:

- Avatars, user cards, the user menu, notifications panel
- The composer, markdown editor, uploads
- Moderation tools, admin UI
- Discourse's own full-page search (`/search` results view) — only the
  header/welcome-banner search *input* is restyled, not the results page
- Discourse's native header itself (see above) — only restyled, not replaced

Only the injected nav, sub-nav, wordmark and footer are bespoke markup.
Everything else stays Discourse, coloured to match.

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

`scripts/sync-from-hal0-web.mjs` regenerates three files from a hal0-web
checkout so tokens and nav links are never hand-typed twice:

| Generated file | Source |
|---|---|
| `stylesheets/_hal0-tokens.scss` | `src/styles/tokens.css` tokens with **no** light override — identical in both schemes (fonts, radii, letter-spacing, motion, shadows) |
| `common/color_definitions.scss` | `src/styles/tokens.css` tokens that **do** have a `[data-theme='light']` override — resolved per Discourse ColorScheme via `dark-light-choose()` (see that file's header) |
| `javascripts/discourse/lib/hal0-nav-data.js` | `src/data/nav.json` (`header`, `footerColumns`, `social`, `footerBase`) |

The tokens.css → SCSS split is structural, not a style choice: `common.scss`
(which pulls in `_hal0-tokens.scss`) compiles **once**, so a token that needs
to differ between light and dark can't live there — it has to be in
`color_definitions.scss`, which Discourse compiles once per `ColorScheme` row
and can therefore resolve differently per scheme. The script partitions on
tokens.css's own `:root` vs `[data-theme='light']` structure, so a token
gains or loses a light override in hal0-web and lands in the right file here
automatically next run — nothing to remember on this side.

```bash
# explicit path
node scripts/sync-from-hal0-web.mjs /path/to/hal0-web

# or via env var
HAL0_WEB_DIR=/mnt/mintdev/repos/hal0-web node scripts/sync-from-hal0-web.mjs

# or rely on the default: ../hal0-web relative to this repo
node scripts/sync-from-hal0-web.mjs
```

All three generated files start with an `AUTO-GENERATED` banner — don't
hand-edit them; edit `hal0-web`'s source files and re-run the script
instead. Run it and commit the diff whenever hal0-web's tokens or nav
change.

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
as a component of the Foundation base theme. That was the component-era
install (see the top of this README) — the full-theme graduation below has
not yet had its own live validation pass; see its still-open items.

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

- [ ] **Deployment model decision, before this ships**: as a component this
      theme layered onto Foundation and inherited 100% of Foundation's CSS,
      only overriding what `stylesheets/_hal0-discourse.scss` targets. As a
      full theme it is installed *instead of* Foundation — Discourse only
      lets components attach to a theme's Components list, not other
      themes, so Foundation and this theme can't both be "the" active theme
      at once. Whatever Foundation was contributing beyond what's covered by
      [What is intentionally NOT themed here](#what-is-intentionally-not-themed-here)
      (spacing tweaks, admin niceties, anything not explicitly restyled
      here) goes away unless this theme is made the site default *and*
      Foundation is kept only as an available alternate in the theme
      selector rather than removed outright. Confirm this is the intended
      tradeoff before installing on `forum.hal0.dev`.
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
- [ ] Manual light/dark toggle (`interface_color_selector`): now wired
      correctly in principle — `common/color_definitions.scss` resolves the
      `--hal0-*` tokens per Discourse `ColorScheme` (via `dark-light-choose`)
      rather than `(prefers-color-scheme: light)`, so they flip in lockstep
      with core's own palette when a visitor forces light/dark
      (`interface-color.js` toggles which of the two compiled
      `color_definitions` stylesheets is active — see
      [Syncing from hal0-web](#syncing-from-hal0-web)). **Not yet verified
      live**: needs `interface_color_selector` turned on
      (Admin → Settings), a scheme with `dark_color_scheme_id` set (see
      [Install](#install) — required for the toggle to even appear;
      `discourse-bootstrap.js` checks for a `link.dark-scheme` stylesheet),
      and a manual toggle-and-inspect pass to confirm both the chrome and
      Discourse's own UI repaint together.

## Forum content model

`scripts/push-content-model.py` builds the forum's structured post types.
It is not part of the theme — it ships here because this repo is already the
place forum configuration lives in git, and the alternative was leaving the
content model in a single Postgres database with no source of truth.

Three post types, each a **core form template** (`enable_form_templates`,
out of experimental since Discourse 2026.02) assigned to categories:

| Template | Categories |
|---|---|
| hal0 · Runner profile | Setups & Profiles |
| hal0 · Benchmark run | Benchmarks |
| hal0 · Hardware report | Strix Halo, NPU / XDNA, Gorgon Halo |

The structured dimensions are **tag groups** bound to `tag-chooser` fields —
Intent, Lane, Model Family, Workload, Quant. This is the part that matters:
a `tag-chooser` answer becomes a real Discourse tag, so it is filterable in
the topic list, browsable at `/tags`, subscribable, and queryable from Data
Explorer. Every other field type is enforced at entry but serialised into the
post body as prose — the schema has only `form_templates` and
`category_form_templates` tables, with no per-topic response storage.

Practical consequence: put anything you will want to **sort or aggregate** on
into a tag group. A numeric field like decode tok/s is captured as text and
is not sortable. If that becomes a real need, the upgrade is
[discourse-custom-wizard](https://github.com/paviliondev/discourse-custom-wizard),
which adds genuinely queryable topic custom fields — and the tag taxonomy
survives that migration unchanged, which is why starting native costs
nothing.

## License

Apache-2.0, matching the hal0 project.
