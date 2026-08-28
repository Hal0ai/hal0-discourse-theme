// The blurb and the "all N topics →" footer on a category card.
//
// Core's categories-boxes-with-topics.gjs renders a heading and the featured
// topics and nothing else — the description belongs to the OTHER box style
// (categories_boxes), which in turn has no topics. hal0.dev/docs shows both
// (its .kbcat cards read: glyph, name, blurb, hairline, pages, "all N pages
// →"), so the theme fills the gap through the outlet core provides for it
// rather than injecting into the DOM after render.
//
// CSS re-orders these above/below .featured-topics — see _hal0-docs.scss.
import Component from "@glimmer/component";

export default class Hal0CategoryBlurb extends Component {
  get category() {
    return this.args?.outletArgs?.category ?? null;
  }

  get blurb() {
    // description_excerpt is the plain-text form the site serializer ships;
    // `description` is cooked HTML, which we deliberately do not render.
    const text =
      this.category?.description_excerpt || this.category?.description_text;
    return text?.trim() || null;
  }

  get allLabel() {
    // Mirrors the hub's "all 12 pages →". The hub knows its page count from
    // a build-time manifest; here it is the category's own topic_count,
    // which excludes the About topic.
    const count = this.category?.topic_count;
    if (!count) {
      return null;
    }
    return `all ${count} ${count === 1 ? "topic" : "topics"} →`;
  }

  <template>
    {{#if this.blurb}}
      <p class="hal0-cat-blurb">{{this.blurb}}</p>
    {{/if}}
    {{#if this.allLabel}}
      <a class="hal0-cat-all" href={{this.category.url}}>{{this.allLabel}}</a>
    {{/if}}
  </template>
}
