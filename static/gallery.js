/*
 * Lightbox for a post's photo gallery.
 *
 * Progressive enhancement: without JavaScript each thumbnail is a plain link
 * to the full-size file, which still works. With it, clicking opens an overlay
 * with previous/next controls on the left and right, arrow-key navigation and
 * Escape to close.
 */
(function () {
  "use strict";

  var grid = document.querySelector("[data-gallery]");
  if (!grid) return;

  var links = Array.prototype.slice.call(
    grid.querySelectorAll("[data-gallery-item]")
  );
  if (!links.length) return;

  var index = 0;
  var lastFocused = null;

  var overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Photo viewer");
  overlay.hidden = true;
  overlay.innerHTML = [
    '<button class="lightbox__close" type="button" aria-label="Close">&times;</button>',
    '<button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Previous photo">&#8249;</button>',
    '<figure class="lightbox__figure">',
    '  <img class="lightbox__image" alt="" />',
    '  <figcaption class="lightbox__caption"></figcaption>',
    "</figure>",
    '<button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Next photo">&#8250;</button>',
  ].join("");
  document.body.appendChild(overlay);

  var image = overlay.querySelector(".lightbox__image");
  var caption = overlay.querySelector(".lightbox__caption");
  var prevButton = overlay.querySelector(".lightbox__nav--prev");
  var nextButton = overlay.querySelector(".lightbox__nav--next");
  var closeButton = overlay.querySelector(".lightbox__close");

  function show(next) {
    // Wrap around, so next on the last photo returns to the first.
    index = (next + links.length) % links.length;
    var link = links[index];
    image.src = link.getAttribute("href");
    image.alt = link.getAttribute("data-caption") || "";
    caption.textContent =
      (link.getAttribute("data-caption") || "") +
      (links.length > 1 ? " (" + (index + 1) + " of " + links.length + ")" : "");
    // Only offer navigation when there is somewhere to go.
    var many = links.length > 1;
    prevButton.hidden = !many;
    nextButton.hidden = !many;
  }

  function open(at) {
    lastFocused = document.activeElement;
    show(at);
    overlay.hidden = false;
    document.body.classList.add("lightbox-open");
    closeButton.focus();
  }

  function close() {
    overlay.hidden = true;
    document.body.classList.remove("lightbox-open");
    image.src = "";
    if (lastFocused) lastFocused.focus();
  }

  links.forEach(function (link, position) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      open(position);
    });
  });

  prevButton.addEventListener("click", function () {
    show(index - 1);
  });
  nextButton.addEventListener("click", function () {
    show(index + 1);
  });
  closeButton.addEventListener("click", close);

  overlay.addEventListener("click", function (event) {
    // A click on the backdrop itself closes; clicks on the photo do not.
    if (event.target === overlay) close();
  });

  document.addEventListener("keydown", function (event) {
    if (overlay.hidden) return;
    if (event.key === "Escape") close();
    else if (event.key === "ArrowLeft") show(index - 1);
    else if (event.key === "ArrowRight") show(index + 1);
  });
})();
