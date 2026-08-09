import Component from "@glimmer/component";
import { htmlSafe } from "@ember/template";
import { HAL0_HEADER_LINKS } from "../../lib/hal0-nav-data";
import { HAL0_WORDMARK_SVG } from "../../lib/hal0-wordmark";

/**
 * hal0-header — brand identity strip for forum.hal0.dev.
 *
 * IMPORTANT scoping note (see README "how the header actually attaches"):
 * `above-main-container` renders BELOW Discourse's own fixed `.d-header`,
 * not above it — there is no outlet above the native header itself. So
 * this connector does NOT replace or hide Discourse's header (search,
 * notifications, hamburger, user menu, "new topic" all stay 100% native,
 * per the design brief's "stays native" list). It adds a second, slimmer
 * strip directly beneath it: the hal0 wordmark, the hal0.dev top nav
 * (learn / benchmarks / profiles), and a "forum" host slug — giving the
 * "one site, not four" continuity the brief asks for without touching
 * Discourse's own interactive chrome.
 */
export default class Hal0Header extends Component {
  wordmark = htmlSafe(HAL0_WORDMARK_SVG);
  links = HAL0_HEADER_LINKS;

  get origin() {
    // `settings` is injected into scope by Discourse's theme compiler for
    // every theme JS file — no import needed. See settings.yml.
    return (typeof settings !== "undefined" && settings.hal0_web_origin) || "https://hal0.dev";
  }

  hrefFor(link) {
    if (link.external || /^https?:\/\//.test(link.href)) {
      return link.href;
    }
    return `${this.origin}${link.href}`;
  }

  get enabled() {
    return typeof settings === "undefined" || settings.show_hal0_chrome !== false;
  }

  <template>
    {{#if this.enabled}}
      <div class="hal0-chrome hdr sticky hal0-brand-strip">
        <div class="wrap wide hdr-in hal0-brand-in">
          <a class="hdr-brand" href={{this.origin}} aria-label="hal0 home">
            {{this.wordmark}}
            <span class="hdr-slug">forum</span>
          </a>
          <nav class="hdr-nav" aria-label="hal0.dev">
            {{#each this.links as |link|}}
              <a href={{this.hrefFor link}} rel="noopener" title="hal0.dev">
                {{link.label}}
                <span class="ext">↗</span>
              </a>
            {{/each}}
          </nav>
        </div>
      </div>
    {{/if}}
  </template>
}
