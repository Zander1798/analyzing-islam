/* =============================================================
   Analyzing Islam — Community editor: media helpers
   -------------------------------------------------------------
   Extends the Quill editor used by community-new-post.js with:
     1. Image/video resizing — click an image or video, and four
        corner handles appear. Drag any corner to resize; aspect
        ratio is preserved (height stays auto) so the image never
        stretches. Width is saved as inline style so the HTML
        serialises cleanly. ✕ remove button lives at the top-right.
     2. Video embeds — a custom Quill "Video" blot (<video
        controls>) so videos can be uploaded and rendered inline.
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

  // ---- 2. Drag-to-resize overlay ----------------------------------
  // When the user clicks an image or video inside the editor, an
  // overlay with 4 corner handles is positioned over the element.
  // Dragging any handle resizes the media by updating its inline
  // style.width in pixels (height stays auto, so aspect ratio is
  // preserved automatically). A ✕ button in the top-right corner
  // removes the media.
  const MIN_WIDTH_PX = 60;

  let activeEl = null;
  let overlay = null;
  let drag = null;

  function ensureOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.className = "cf-media-resize";
    overlay.innerHTML =
      '<button type="button" class="cf-media-resize-remove" data-action="remove" aria-label="Remove media">✕</button>' +
      '<span class="cf-media-resize-handle" data-dir="nw" aria-hidden="true"></span>' +
      '<span class="cf-media-resize-handle" data-dir="ne" aria-hidden="true"></span>' +
      '<span class="cf-media-resize-handle" data-dir="sw" aria-hidden="true"></span>' +
      '<span class="cf-media-resize-handle" data-dir="se" aria-hidden="true"></span>';

    // Don't steal focus from the editor when clicking the overlay.
    overlay.addEventListener("mousedown", (e) => e.preventDefault());

    overlay.querySelector('[data-action="remove"]').addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      removeActive();
    });

    overlay.querySelectorAll(".cf-media-resize-handle").forEach((h) => {
      h.addEventListener("mousedown", onHandleDown);
      h.addEventListener("touchstart", onHandleDown, { passive: false });
    });

    document.body.appendChild(overlay);
    return overlay;
  }

  // -------- Drag lifecycle --------
  function onHandleDown(e) {
    if (!activeEl) return;
    e.preventDefault();
    e.stopPropagation();
    const handle = e.currentTarget;
    const dir = handle.getAttribute("data-dir");
    const point = e.touches ? e.touches[0] : e;
    const rect = activeEl.getBoundingClientRect();
    drag = {
      dir,
      startX: point.clientX,
      startWidth: rect.width,
      parentWidth: activeEl.parentElement
        ? activeEl.parentElement.getBoundingClientRect().width
        : window.innerWidth,
    };
    document.addEventListener("mousemove", onDragMove);
    document.addEventListener("mouseup", onDragUp);
    document.addEventListener("touchmove", onDragMove, { passive: false });
    document.addEventListener("touchend", onDragUp);
  }

  function onDragMove(e) {
    if (!drag || !activeEl) return;
    e.preventDefault();
    const point = e.touches ? e.touches[0] : e;
    const dx = point.clientX - drag.startX;
    // Left-side handles (nw, sw) grow the width when dragged left.
    const sign = drag.dir.indexOf("w") !== -1 ? -1 : 1;
    let newWidth = drag.startWidth + dx * sign;
    // Clamp between the minimum and the available parent width so the
    // image never overflows the editor column.
    newWidth = Math.max(MIN_WIDTH_PX, Math.min(newWidth, drag.parentWidth));
    activeEl.style.width = Math.round(newWidth) + "px";
    activeEl.style.height = "auto";
    activeEl.style.maxWidth = "100%";
    reposition();
  }

  function onDragUp() {
    drag = null;
    document.removeEventListener("mousemove", onDragMove);
    document.removeEventListener("mouseup", onDragUp);
    document.removeEventListener("touchmove", onDragMove);
    document.removeEventListener("touchend", onDragUp);
  }

  function removeActive() {
    if (!activeEl) return;
    const el = activeEl;
    deselect();
    el.remove();
  }

  function reposition() {
    if (!overlay || !activeEl || !activeEl.isConnected) return;
    const r = activeEl.getBoundingClientRect();
    overlay.style.top = (r.top + window.scrollY) + "px";
    overlay.style.left = (r.left + window.scrollX) + "px";
    overlay.style.width = r.width + "px";
    overlay.style.height = r.height + "px";
  }

  function select(el) {
    if (activeEl && activeEl !== el) deselect();
    activeEl = el;
    activeEl.classList.add("cf-media-selected");
    ensureOverlay();
    overlay.classList.add("is-open");
    reposition();
  }

  function deselect() {
    if (activeEl) activeEl.classList.remove("cf-media-selected");
    activeEl = null;
    if (overlay) overlay.classList.remove("is-open");
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

    // Keep the overlay parked against the media as the page reflows.
    window.addEventListener("scroll", reposition, { passive: true });
    window.addEventListener("resize", reposition);

    // Click outside the editor / overlay → deselect.
    document.addEventListener("mousedown", (e) => {
      if (!activeEl) return;
      if (editorRoot.contains(e.target)) return;
      if (overlay && overlay.contains(e.target)) return;
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
