import Component from "@glimmer/component";
import { htmlSafe } from "@ember/template";
import { HAL0_WORDMARK_SVG } from "../../lib/hal0-wordmark";

/**
 * hal0-wordmark — replaces the uploaded site logo with the inline wordmark.
 *
 * The `logo` site setting points at public/brand/logo-halo-dark.svg, whose
 * artboard is a 1500x1500 square. As an <img> there is no way to crop it,
 * so at the comp's 19px lockup height it rendered as a 19x19 square with
 * illegible lettering inside — the same trap this repo already hit with the
 * inlined copy, except an <img> cannot be fixed with a viewBox.
 *
 * hal0-wordmark.js carries the same artwork already cropped to the band the
 * lettering occupies, with "hal" on currentColor and the "0" on
 * var(--hal0-accent). Rendering that here means the forum's wordmark is the
 * identical vector hal0.dev draws, tracks the brand token, and inherits the
 * header's foreground colour in either scheme.
 */
export default class Hal0Wordmark extends Component {
  wordmark = htmlSafe(HAL0_WORDMARK_SVG);

  get enabled() {
    return typeof settings === "undefined" || settings.show_hal0_chrome !== false;
  }

  <template>
    {{#if this.enabled}}
      <span class="hal0-chrome hal0-home-wordmark">{{this.wordmark}}</span>
    {{/if}}
  </template>
}
