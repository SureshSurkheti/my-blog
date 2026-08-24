/*
 * Collapses the header search into an icon.
 *
 * Progressive enhancement: the form is visible by default, so with JavaScript
 * off it stays a plain, working search box. This script marks the document as
 * scripted (which is what lets the CSS collapse the form) and reveals the
 * toggle button.
 */
(function () {
  "use strict";

  var form = document.querySelector("[data-nav-search]");
  var toggle = document.querySelector("[data-nav-search-toggle]");
  if (!form || !toggle) return;

  var input = form.querySelector('input[type="search"]');
  document.documentElement.classList.add("js-nav");
  toggle.hidden = false;

  function setOpen(open) {
    form.classList.toggle("nav-search--open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open && input) input.focus();
  }

  toggle.addEventListener("click", function () {
    setOpen(!form.classList.contains("nav-search--open"));
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    if (!form.classList.contains("nav-search--open")) return;
    setOpen(false);
    toggle.focus();
  });

  document.addEventListener("click", function (event) {
    if (!form.classList.contains("nav-search--open")) return;
    if (form.contains(event.target) || toggle.contains(event.target)) return;
    setOpen(false);
  });

  // A search that returned results keeps the field open, so the term stays
  // visible next to its results.
  if (input && input.value.trim()) setOpen(true);
})();
