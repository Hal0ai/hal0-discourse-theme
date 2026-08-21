import Component from "@glimmer/component";
import { service } from "@ember/service";

/**
 * hal0-subnav — the comp's second bar.
 *
 * `07 Forum.html` renders exactly two bars: `<Header variant="forum" />`
 * and, directly beneath it, `<div className="subnav">` carrying the forum's
 * own view tabs plus a link back to hal0.dev. This is that second bar.
 *
 * It attaches to `after-header`, which renders inside `<header class="d-header">`
 * after the header row — so the sub-nav travels with the sticky header
 * instead of scrolling away from it, and no separate sticky context is
 * created (two stacked `position: sticky` elements was a known risk in the
 * README's validation list; this sidesteps it entirely).
 *
 * The tabs are plain links to Discourse routes rather than a re-implementation
 * of its navigation: /latest, /top, /categories and /my/activity are all real
 * routes, so this stays a skin over Discourse rather than a fork of it.
 */
const TABS = [
  { label: "latest", href: "/latest", route: "discovery.latest" },
  { label: "top", href: "/top", route: "discovery.top" },
  { label: "categories", href: "/categories", route: "discovery.categories" },
  { label: "my posts", href: "/my/activity", route: null },
];

export default class Hal0Subnav extends Component {
  @service router;

  tabs = TABS;

  get enabled() {
    return typeof settings === "undefined" || settings.show_hal0_chrome !== false;
  }

  get origin() {
    return (typeof settings !== "undefined" && settings.hal0_web_origin) || "https://hal0.dev";
  }

  isCurrent = (tab) => {
    const path = this.router.currentURL || "";
    if (tab.href === "/latest") {
      // "/" and "/latest" are the same view; Discourse's root route depends
      // on the top_menu setting, so match both rather than guessing.
      return path === "/" || path.startsWith("/latest");
    }
    return path.startsWith(tab.href);
  };

  <template>
    {{#if this.enabled}}
      <div class="hal0-chrome hal0-subnav">
        <div class="wrap wide hal0-subnav-in">
          {{#each this.tabs as |tab|}}
            <a
              href={{tab.href}}
              aria-current={{if (this.isCurrent tab) "page"}}
            >{{tab.label}}</a>
          {{/each}}
          <a class="hal0-subnav-away" href={{this.origin}} rel="noopener">
            hal0.dev
            <span class="ext">↗</span>
          </a>
        </div>
      </div>
    {{/if}}
  </template>
}
