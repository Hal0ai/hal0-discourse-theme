import { apiInitializer } from "discourse/lib/api";

/**
 * hal0-toml-download — adds a "download .toml" button to fenced ```toml
 * code blocks in posts.
 *
 * This is how the runner-profile registry gets consumed: a wiki first post
 * carries the canonical TOML for a profile in a fenced block, and readers
 * grab it as a file instead of copy-pasting out of a <pre>. The download is
 * client-side only (Blob + object URL, no request to hal0-web or the
 * forum) and the filename is derived from the topic slug so a saved file is
 * immediately recognisable.
 *
 * Discourse's markdown pipeline (via highlight.js) renders a fenced ```toml
 * block as `<pre><code class="lang-toml">…</code></pre>`, so that's the
 * exact selector decorateCookedElement is asked to find.
 */
export default apiInitializer((api) => {
  const enabled = () =>
    typeof settings === "undefined" || settings.show_hal0_chrome !== false;

  const slugify = (value) =>
    (value || "")
      .toString()
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

  const topicSlugFor = (helper) => {
    const post = helper?.model;
    const fromModel = post?.topic?.slug || post?.topic_slug;
    if (fromModel) {
      return slugify(fromModel);
    }
    // Fallback for contexts where the post model isn't wired to a topic yet
    // (e.g. a decorator running ahead of the post-stream finishing setup):
    // topic routes are always /t/<slug>/<id>, so pull it from the URL.
    const match = window.location.pathname.match(/\/t\/([^/]+)\/\d+/);
    return match ? slugify(match[1]) : "";
  };

  const downloadToml = (filename, contents) => {
    const blob = new Blob([contents], { type: "application/toml" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  api.decorateCookedElement((element, helper) => {
    if (!enabled()) {
      return;
    }

    const blocks = element.querySelectorAll("pre code.lang-toml");
    if (!blocks.length) {
      return;
    }

    const baseSlug = topicSlugFor(helper) || "runner-profile";

    blocks.forEach((code, index) => {
      const pre = code.closest("pre");
      if (!pre || pre.querySelector(".hal0-toml-download")) {
        return;
      }

      const suffix = blocks.length > 1 ? `-${index + 1}` : "";
      const filename = `${baseSlug}${suffix}.toml`;

      const button = document.createElement("button");
      button.type = "button";
      button.className = "hal0-toml-download";
      button.textContent = "download .toml";
      button.setAttribute("aria-label", `Download ${filename}`);
      button.addEventListener("click", () => {
        downloadToml(filename, code.textContent || "");
      });

      pre.classList.add("hal0-toml-block");
      pre.appendChild(button);
    });
  });
});
