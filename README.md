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
  _hal0-tokens.scss                           AUTO-GENERATED — brand tokens as CSS custom properties
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
LICENSE                                       Apache-2.0, matching the hal0 project
```

## Install

Discourse admin → **Customize → Themes → Install → From a git repository**:

```
https://github.com/Hal0ai/hal0-discourse-theme
```

Install it as a **component**, then add it to whatever theme is active on
`forum.hal0.dev` (Themes → your active theme → Components → add "hal0 forum
theme"). Under the theme's **Colors** tab, set the default color scheme to
"hal0 dark" (and, if the forum offers a light/dark toggle, "hal0 light" as
the alternate scheme).

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
| `common/_hal0-tokens.scss` | `src/styles/tokens.css` (`:root` + `[data-theme='light']` blocks) |
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
  token names, so those hex values are hand-transcribed from
  `tokens.css`. If hal0's palette changes, update `about.json` too.
- `javascripts/discourse/lib/hal0-wordmark.js` and `hal0-icons.js` — the
  wordmark and github/discord/rss glyphs, copied once from
  `public/brand/logo-halo-dark.svg` and `site-chrome.jsx`'s `BrandIcon`.
  These change rarely enough that a sync step wasn't worth building.
- The footer base line's version string
  (`Apache-2.0 · hal0 v0.5.0a1 · 1.0.0-RC.3`, hardcoded in
  `hal0-footer.gjs`) — per the design brief this must match `BINARY` in
  `hal0-web/src/data/model-roster.ts` and the homepage hero pill. There's no
  automated source for it in this repo yet; update it by hand when hal0 cuts
  a release, or wire a future sync step to `model-roster.ts` if it drifts
  often enough to be annoying.

## Validation (deferred to launch)

**There is no live Discourse instance to test against.** Everything above is
built against the design comp, `nav.json`/`tokens.css`, and Discourse's
documented plugin-outlet / theme-component conventions — not verified in a
running forum. Before calling this done:

- [ ] Install on the actual `forum.hal0.dev` Discourse (or a staging copy)
      via the git-repo installer above.
- [ ] Screenshot the categories index, a topic list, and an open topic;
      compare against `07 Forum.html`'s `CategoryIndex` / `TopicList` /
      `TopicView` states (the header/footer strip is this theme's job — the
      topic rows/badges/avatars in between are Discourse's own components
      restyled by the color scheme, so check those too, they're not exempt
      from the comparison just because this repo didn't write their markup).
- [ ] Confirm the brand strip's sticky/backdrop-blur behavior doesn't fight
      with Discourse's own sticky header (two stacked `position: sticky`
      elements can behave oddly depending on Discourse's header height and
      scroll-shrink behavior on mobile).
- [ ] Confirm `html.light-scheme` is in fact the class Discourse's core adds
      when a user or the OS prefers light mode — `_hal0-tokens.scss`'s light
      override selector is a best guess based on newer Discourse core
      conventions and is explicitly unverified (see the comment at the top
      of that file).
- [ ] Decide whether the brand-strip-below-native-header approach (see
      [How the header actually attaches](#how-the-header-actually-attaches))
      is acceptable, or whether full header replacement is required — and if
      so, scope that as separate follow-up work.
- [ ] Verify the footer's hardcoded version string against the live
      `BINARY` value at launch time.
- [ ] Check the `⌘K` / `/` search keyboard shortcut and Discourse's own
      search still work unobstructed with the extra strip in the DOM.
- [ ] Mobile: confirm the brand strip's nav links don't create a confusing
      double-hamburger situation next to Discourse's own mobile header
      controls.

## License

Apache-2.0, matching the hal0 project.
