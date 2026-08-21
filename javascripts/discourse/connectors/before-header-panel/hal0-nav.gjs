import Component from "@glimmer/component";
import { service } from "@ember/service";
import { HAL0_HEADER_LINKS } from "../../lib/hal0-nav-data";

/**
 * hal0-nav — the hal0.dev top nav, rendered INSIDE Discourse's own header.
 *
 * `before-header-panel` sits in header/contents.gjs between the home logo
 * and the panel that carries search, notifications and the user menu. That
 * ordering is exactly the design comp's forum-variant header:
 *
 *   [ wordmark | forum ]  learn  benchmarks  profiles  forum      [ search ⌕  ◎  ● ]
 *
 * An earlier version of this component injected a whole second brand strip
 * into `above-main-container` instead. That outlet renders *below* the
 * native header, so the result was two stacked bars, the hal0 wordmark
 * drawn twice, and a mostly empty 56px band — see the README. Everything
 * that strip carried now lives here, in the one real header, and the strip
 * itself has been replaced by the comp's sub-nav (hal0-subnav.gjs).
 *
 * Discourse's own controls are untouched: search, notifications, hamburger
 * and the user menu remain 100% native, which the design brief requires.
 */
export default class Hal0Nav extends Component {
  @service router;

  links = HAL0_HEADER_LINKS;

  get origin() {
    return (typeof settings !== "undefined" && settings.hal0_web_origin) || "https://hal0.dev";
  }

  get enabled() {
    return typeof settings === "undefined" || settings.show_hal0_chrome !== false;
  }

  // Arrow function: invoked from the template as a helper, so a plain
  // method would lose its receiver (see the footer connector).
  hrefFor = (link) => {
    if (link.external || /^https?:\/\//.test(link.href)) {
      return link.href;
    }
    return `${this.origin}${link.href}`;
  };

  <template>
    {{#if this.enabled}}
      <div class="hal0-chrome hal0-hdr-nav">
        <span class="hdr-slug">forum</span>
        <nav class="hdr-nav" aria-label="hal0.dev">
          {{#each this.links as |link|}}
            <a href={{this.hrefFor link}} rel="noopener" title="hal0.dev">
              {{link.label}}
              <span class="ext">↗</span>
            </a>
          {{/each}}
          {{! The forum is the surface you are already on, so it is marked
              current rather than linked away. The comp keeps it in the nav
              and highlights it here. }}
          <a href="/" aria-current="page">forum</a>
        </nav>
      </div>
    {{/if}}
  </template>
}
