/* =============================================================
   Analyzing Islam — Community editor: media helpers
   -------------------------------------------------------------
   Extends the Quill editor used by community-new-post.js with:
     1. Image resizing — click an image and pick Small / Medium /
        Large / Full from a floating toolbar. Width is saved as
        an inline style so the HTML serialises cleanly.
     2. Video embeds — a custom Quill "Video" blot (<video
        controls>) so videos can be uploaded and rendered inline
        in posts. Same resize toolbar works on videos.
   ============================================================= */
(function () {
  "use strict";

  if (!window.Quill) return;

  // ---- 1. Custom Video blot (Quill format) ------------------------
  const BlockEmbed = Quill.import("blots/block/embed");

  class VideoBlot extends BlockEmbed {
    static create(value) {
      const node = super.create();
      const src = typeof value === "string" ? value : value && value.src;
      node.setAttribute("src", src);
      node.setAttribute("controls", "controls");
      node.setAttribute("playsinline", "");
      node.setAttribute("preload", "metadata");
      if (value && value.width) node.style.width = value.width;
      return node;
    }
    static value(node) {
      return {
        src: node.getAttribute("src"),
        width: node.style.width || null,
      };
    }
  }
  VideoBlot.blotName = "cf-video";
  VideoBlot.tagName = "video";
  VideoBlot.className = "cf-post-video";

  // Register once, globally.
  if (!Quill.imports["formats/cf-video"]) {
    Quill.register({ "formats/cf-video": VideoBlot }, true);
  }

  // ---- 2. Floating size toolbar -----------------------------------
  // Appears next to the currently-selected image or video inside the
  // editor. Choices are width presets that map to CSS percentages so
  // posts render consistently on any viewport width.
  const PRESETS = [
    { label: "S",    width: "25%" },
    { label: "M",    width: "50%" },
    { label: "L",    width: "75%" },
    { label: "Full", width: "100%" },
  ];

  let activeEl = null;
  let bar = null;

  function ensureBar() {
    if (bar) return bar;
    bar = document.createElement("div");
    bar.className = "cf-media-bar";
    bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", "Media size");
    bar.innerHTML =
      PRESETS.map((p) =>
        `<button type="button" data-w="${p.width}" aria-label="${p.label}">${p.label}</button>`
      ).join("") +
      `<span class="cf-media-bar-sep" aria-hidden="true"></span>` +
      `<button type="button" data-action="remove" aria-label="Remove media">✕</button>`;
    bar.addEventListener("mousedown", (e) => {
      // Stop the editor from losing its selection when clicking the bar.
      e.preventDefault();
    });
    bar.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn || !activeEl) return;
      if (btn.getAttribute("data-action") === "remove") {
        removeActive();
        return;
      }
      const w = btn.getAttribute("data-w");
      if (w) setWidth(activeEl, w);
      // Re-position in case reflow changed things.
      position();
      markActiveFromElement();
    });
    document.body.appendChild(bar);
    return bar;
  }

  function markActiveFromElement() {
    if (!bar || !activeEl) return;
    const current = activeEl.style.width;
    bar.querySelectorAll("button[data-w]").forEach((b) => {
      b.classList.toggle("is-active", b.getAttribute("data-w") === current);
    });
  }

  function setWidth(el, w) {
    // Store on the element as inline style — Quill serialises this in the
    // output HTML, so posts render at the author-chosen width without
    // needing a separate DB column.
    el.style.width = w;
    el.style.height = "auto";
    // Keep a sane minimum so Small doesn't shrink to a thumbnail on phones.
    el.style.maxWidth = "100%";
  }

  function removeActive() {
    if (!activeEl) return;
    const el = activeEl;
    deselect();
    el.remove();
  }

  function position() {
    if (!bar || !activeEl || !activeEl.isConnected) return;
    const r = activeEl.getBoundingClientRect();
    const barH = bar.offsetHeight || 36;
    const top = Math.max(8, r.top + window.scrollY - barH - 8);
    const left = Math.max(8, r.left + window.scrollX + r.width / 2 - (bar.offsetWidth || 160) / 2);
    bar.style.top = top + "px";
    bar.style.left = left + "px";
  }

  function select(el) {
    if (activeEl && activeEl !== el) deselect();
    activeEl = el;
    activeEl.classList.add("cf-media-selected");
    ensureBar();
    bar.classList.add("is-open");
    position();
    markActiveFromElement();
  }

  function deselect() {
    if (activeEl) activeEl.classList.remove("cf-media-selected");
    activeEl = null;
    if (bar) bar.classList.remove("is-open");
  }

  // ---- 3. Public helper: attach all of this to a Quill instance ---
  // community-new-post.js calls this after it instantiates a Quill on
  // a target, passing the root element.
  function attach(editorRoot) {
    if (!editorRoot) return;

    editorRoot.addEventListener("click", (e) => {
      const el = e.target.closest("img, video");
      if (el && editorRoot.contains(el)) {
        e.stopPropagation();
        select(el);
      } else {
        deselect();
      }
    });

    // Keep the bar parked against the media as the page reflows.
    window.addEventListener("scroll", position, { passive: true });
    window.addEventListener("resize", position);

    // Click outside the editor/bar → deselect.
    document.addEventListener("mousedown", (e) => {
      if (!activeEl) return;
      if (editorRoot.contains(e.target)) return;
      if (bar && bar.contains(e.target)) return;
      deselect();
    });
  }

  // ---- 4. Upload a video file to Storage and insert into Quill ----
  async function uploadAndInsertVideo(quill, file) {
    if (!window.COMMUNITY_API || typeof COMMUNITY_API.uploadImage !== "function") {
      alert("Upload helper not ready. Refresh and try again.");
      return;
    }
    if (!/^video\//i.test(file.type)) {
      alert("Please pick a video file.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      alert("Video must be 50 MB or smaller.");
      return;
    }
    const range = quill.getSelection(true);
    quill.insertText(range.index, "Uploading video…", "italic", true);
    // Reuse uploadImage: Supabase storage doesn't actually care about
    // image-vs-video at the API layer, and the same bucket can hold
    // either. community-post-images is already public-read + owner-write.
    const up = await COMMUNITY_API.uploadImage("community-post-images", file);
    quill.deleteText(range.index, "Uploading video…".length);
    if (up.error) {
      alert("Video upload failed: " + (up.error.message || up.error));
      return;
    }
    quill.insertEmbed(range.index, "cf-video", up.url, "user");
    quill.setSelection(range.index + 1, 0);
  }

  function pickAndUploadVideo(quill) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/*";
    input.onchange = () => {
      const f = input.files && input.files[0];
      if (!f) return;
      uploadAndInsertVideo(quill, f);
    };
    input.click();
  }

  // Expose a small API the new-post script hooks into.
  window.CF_EDITOR_MEDIA = {
    attach,
    pickAndUploadVideo,
    select,
    deselect,
  };
})();
