import Component from "@glimmer/component";
import { htmlSafe } from "@ember/template";
import { HAL0_FOOTER_COLUMNS, HAL0_SOCIAL, HAL0_FOOTER_BASE } from "../../lib/hal0-nav-data";
import { HAL0_WORDMARK_SVG } from "../../lib/hal0-wordmark";
import { HAL0_ICON_PATHS } from "../../lib/hal0-icons";

// Hand-maintained — mirrors SiteFooter.astro's `footerVersion`, which comes
// from parseChangelog() over hal0-web/src/data/changelog.md's latest
// `## [x.y.z]` header (currently "1.0.0-rc.3"). The sync script doesn't
// parse changelog.md yet, so this has to be bumped by hand when hal0-web's
// changelog gains a new latest version — check it against changelog.md at
// launch time and whenever this theme is updated afterward.
const FOOTER_VERSION = "1.0.0-rc.3";

/**
 * hal0-footer — the shared brand footer, identical to every other hal0.dev
 * surface (see SiteFooter.astro). Injected via `below-footer` so it sits
 * after Discourse's own footer content, closing out the page the same way
 * hal0.dev does.
 *
 * Do NOT gate this on Discourse's own footer visibility. Core's
 * `below-footer` outlet (application.gjs) renders unconditionally; it is
 * Discourse's OWN footer content — `<PoweredByDiscourse />` and the custom
 * "footer" HTML block — that is conditional, on `@controller.showFooter`,
 * which reads the `footer` service's hider registry. `discovery/topics.gjs`
 * (the component behind `/`, `/latest`, `/top`, `/new`) holds a hider open
 * via `{{hideApplicationFooter}}` for as long as the topic list has more
 * pages to infinite-scroll; none of the six `/categories` display
 * components ever call that helper, so `/categories` shows its footer
 * immediately while `/` can sit with showFooter=false for a while. This
 * component has no route/service dependency at all (unlike hal0-nav.gjs /
 * hal0-subnav.gjs, which inject `@service router`) — it should render
 * identically regardless of that state, and the CSS in common.scss
 * (`.hal0-chrome.ftr`) is written to not assume a preceding native-footer
 * sibling supplies its box/spacing.
 */
export default class Hal0Footer extends Component {
  wordmark = htmlSafe(HAL0_WORDMARK_SVG);
  columns = HAL0_FOOTER_COLUMNS;
  social = HAL0_SOCIAL;
  footerBase = HAL0_FOOTER_BASE;
  footerVersion = FOOTER_VERSION;

  get rssLink() {
    return this.footerBase.find((l) => l.label === "rss");
  }

  get changelogLink() {
    return this.footerBase.find((l) => l.label === "changelog");
  }

  get origin() {
    return (typeof settings !== "undefined" && settings.hal0_web_origin) || "https://hal0.dev";
  }

  // Arrow functions, not methods: both are invoked from the template as
  // `{{this.hrefFor l}}` / `{{this.iconSvg s.id}}`, and a plain method loses
  // its receiver when called that way (`this` is undefined inside it, so
  // `this.origin` throws). Arrow class fields close over the instance.
  hrefFor = (link) => {
    if (link.external || /^https?:\/\//.test(link.href) || link.href.startsWith("mailto:")) {
      return link.href;
    }
    return `${this.origin}${link.href}`;
  };

  iconSvg = (id) => {
    const path = HAL0_ICON_PATHS[id];
    if (!path) {
      // Silently rendering nothing here would hide a real problem: it means
      // nav.json's `social` (or the rss entry) grew an id this repo's
      // hand-copied hal0-icons.js doesn't know about yet. Warn so whoever
      // runs the sync script next notices instead of shipping a blank icon.
      // eslint-disable-next-line no-console
      console.warn(`[hal0-theme] no icon glyph for id "${id}" — add it to hal0-icons.js`);
      return htmlSafe("");
    }
    return htmlSafe(
      `<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="${path}"/></svg>`
    );
  };

  get enabled() {
    return typeof settings === "undefined" || settings.show_hal0_chrome !== false;
  }

  <template>
    {{#if this.enabled}}
      <footer class="hal0-chrome ftr">
        <div class="wrap wide">
          <div class="ftr-cols">
            <div class="ftr-brand">
              {{this.wordmark}}
              <p class="site-sm" style="margin-top: 12px;">
                Self-hosted AI inference for the box in your rack. Built and benchmarked by the
                Strix Halo community.
              </p>
              <div style="display: flex; gap: 6px; margin-top: 14px;">
                {{#each this.social as |s|}}
                  <a class="iconbtn" href={{s.href}} rel="noopener" aria-label={{s.label}}>{{this.iconSvg
                      s.id
                    }}</a>
                {{/each}}
                {{#if this.rssLink}}
                  <a class="iconbtn" href={{this.hrefFor this.rssLink}} aria-label="RSS">{{this.iconSvg
                      "rss"
                    }}</a>
                {{/if}}
              </div>
            </div>
            {{#each this.columns as |col|}}
              <div class="ftr-col">
                <h4 class="label">{{col.heading}}</h4>
                <ul>
                  {{#each col.links as |l|}}
                    <li>
                      <a href={{this.hrefFor l}} rel={{if l.external "noopener"}}>
                        {{l.label}}
                        {{#if l.external}}<span> ↗</span>{{/if}}
                      </a>
                    </li>
                  {{/each}}
                </ul>
              </div>
            {{/each}}
          </div>
          <div class="ftr-base">
            <span>Apache-2.0 · {{this.footerVersion}}</span>
            <span>
              {{#if this.changelogLink}}
                <a href={{this.hrefFor this.changelogLink}}>{{this.changelogLink.label}}</a>
              {{/if}}
            </span>
          </div>
        </div>
      </footer>
    {{/if}}
  </template>
}
