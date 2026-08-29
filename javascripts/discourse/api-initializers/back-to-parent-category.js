import { apiInitializer } from "discourse/lib/api";

// The docs sidebar's back link.
//
// Core renders it as `<BackToForum />` inside the sidebar panel header
// (components/sidebar/back-to-forum.gjs) with the label hard-coded to
// i18n `sidebar.back_to_forum` and the href defaulting to "/". The panel
// itself belongs to discourse-doc-categories, so a theme cannot pass the
// component's `@href` arg, and there is no plugin outlet on that row --
// hence the DOM update below rather than a connector.
//
// Behaviour: one level up, not all the way out. Inside a docs or KB
// SECTION (a subcategory, or a topic in one) the link goes back to the
// parent category — "Back to Docs" — because that is where the reader
// came from. On the parent category itself the link is left alone, since
// from there the forum IS one level up.
export default apiInitializer((api) => {
  const site = api.container.lookup("service:site");
  const router = api.container.lookup("service:router");

  function categoryIdFromRoute() {
    // Category routes carry "<parent>/<child>/<id>"; the id is the last
    // segment and is the only part guaranteed unique.
    for (let route = router.currentRoute; route; route = route.parent) {
      const path = route.params?.category_slug_path_with_id;
      if (path) {
        const id = parseInt(path.split("/").pop(), 10);
        if (!isNaN(id)) {
          return id;
        }
      }
    }
    // Topic routes have no category in their params; the model does.
    return api.container.lookup("controller:topic")?.model?.category?.id ?? null;
  }

  function parentCategory() {
    const id = categoryIdFromRoute();
    if (!id) {
      return null;
    }
    const category = site.categories?.find((c) => c.id === id);
    if (!category?.parent_category_id) {
      return null; // top-level category: "back to forum" is already right
    }
    return site.categories.find((c) => c.id === category.parent_category_id);
  }

  api.onPageChange(() => {
    // The sidebar renders after the route settles, so read on the next frame.
    requestAnimationFrame(() => {
      const link = document.querySelector(".sidebar-sections__back-to-forum");
      if (!link) {
        return;
      }
      const label = link.querySelector("span");
      if (!label) {
        return;
      }

      // Remember the original once, so leaving a section restores it rather
      // than leaving "Back to Docs" behind on an unrelated page.
      if (!link.dataset.hal0DefaultLabel) {
        link.dataset.hal0DefaultLabel = label.textContent;
        link.dataset.hal0DefaultHref = link.getAttribute("href") ?? "/";
      }

      const parent = parentCategory();
      if (parent) {
        label.textContent = `Back to ${parent.name}`;
        link.setAttribute("href", `/c/${parent.slug}/${parent.id}`);
      } else {
        label.textContent = link.dataset.hal0DefaultLabel;
        link.setAttribute("href", link.dataset.hal0DefaultHref);
      }
    });
  });
});
