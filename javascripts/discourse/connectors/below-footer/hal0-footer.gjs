import Component from "@glimmer/component";
import { htmlSafe } from "@ember/template";
import { HAL0_FOOTER_COLUMNS, HAL0_SOCIAL, HAL0_FOOTER_BASE } from "../../lib/hal0-nav-data";
import { HAL0_WORDMARK_SVG } from "../../lib/hal0-wordmark";
import { HAL0_ICON_PATHS } from "../../lib/hal0-icons";

/**
 * hal0-footer — the shared brand footer, identical to every other hal0.dev
 * surface (see SiteFooter.astro). Injected via `below-footer` so it sits
 * after Discourse's own footer content, closing out the page the same way
 * hal0.dev does.
 */
export default class Hal0Footer extends Component {
  wordmark = htmlSafe(HAL0_WORDMARK_SVG);
  columns = HAL0_FOOTER_COLUMNS;
  social = HAL0_SOCIAL;
  footerBase = HAL0_FOOTER_BASE;

  get rssLink() {
    return this.footerBase.find((l) => l.label === "rss");
  }

  get origin() {
    return (typeof settings !== "undefined" && settings.hal0_web_origin) || "https://hal0.dev";
  }

  hrefFor(link) {
    if (link.external || /^https?:\/\//.test(link.href) || link.href.startsWith("mailto:")) {
      return link.href;
    }
    return `${this.origin}${link.href}`;
  }

  iconSvg(id) {
    const path = HAL0_ICON_PATHS[id];
    if (!path) {
      return htmlSafe("");
    }
    return htmlSafe(
      `<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="${path}"/></svg>`
    );
  }

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
            <span>Apache-2.0 · hal0 v0.5.0a1 · 1.0.0-RC.3</span>
            <span style="display: inline-flex; align-items: center; gap: 8px;">
              <span class="dot ready"></span> all systems steady
            </span>
          </div>
        </div>
      </footer>
    {{/if}}
  </template>
}
