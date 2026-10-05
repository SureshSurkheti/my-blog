/*
 * The light/dark switch.
 *
 * The page already follows the operating system through prefers-color-scheme;
 * this is for the reader who wants something other than what their system
 * says — a dark phone at a bright desk, or the reverse.
 *
 * Progressive enhancement, the same shape as nav.js: the button ships hidden
 * and is revealed here, so with JavaScript off nobody is offered a control
 * that cannot work. The system preference still applies in that case.
 *
 * The choice is stored under "theme" and read back by the inline script in
 * the document head, which runs before the first paint. Doing it here instead
 * would show the wrong theme for a frame — the white flash that makes a dark
 * site feel broken.
 */
(function () {
  "use strict";

  var KEY = "theme";
  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;

  var root = document.documentElement;
  var label = button.querySelector("[data-theme-label]");

  function stored() {
    try {
      var value = window.localStorage.getItem(KEY);
      return value === "dark" || value === "light" ? value : null;
    } catch (error) {
      // Private browsing, or storage disabled. The switch still works for
      // this page view; it just will not be remembered.
      return null;
    }
  }

  function systemPrefersDark() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }

  function current() {
    return root.dataset.theme || (systemPrefersDark() ? "dark" : "light");
  }

  function apply(theme) {
    root.dataset.theme = theme;
    // aria-pressed would claim the button is a dark-mode checkbox that is on
    // or off; it is really a switch between two named states, so the label
    // says which one a press would bring.
    var next = theme === "dark" ? "light" : "dark";
    button.setAttribute("aria-label", "Switch to " + next + " mode");
    button.setAttribute("title", "Switch to " + next + " mode");
    if (label) label.textContent = next === "dark" ? "Dark" : "Light";
    button.dataset.themeState = theme;
  }

  // The head script sets data-theme only when a choice was stored. Fill it in
  // from the system so the first press is never a no-op.
  apply(stored() || current());
  button.hidden = false;

  button.addEventListener("click", function () {
    var next = current() === "dark" ? "light" : "dark";
    apply(next);
    try {
      window.localStorage.setItem(KEY, next);
    } catch (error) {
      /* nothing to do; the page is already switched */
    }
  });

  // Follow the system while the reader has expressed no preference of their
  // own, so changing the phone's setting at sunset changes the page too.
  if (window.matchMedia) {
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", function (event) {
        if (stored()) return;
        apply(event.matches ? "dark" : "light");
      });
  }
})();
