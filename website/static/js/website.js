(function () {
  var STORAGE_KEY = "theme";
  var root = document.documentElement;

  function storedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function applyTheme(theme) {
    if (theme === "dark" || theme === "light") {
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  // Applied immediately (this script is loaded synchronously in <head>) so
  // a stored preference takes effect before first paint - no flash of the
  // wrong theme.
  applyTheme(storedTheme());

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("theme-toggle");
    if (!button) {
      return;
    }

    function isDark() {
      var explicit = root.getAttribute("data-theme");
      if (explicit) {
        return explicit === "dark";
      }
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    function syncButton() {
      button.setAttribute("aria-pressed", String(isDark()));
    }

    button.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        // Storage unavailable (private browsing, disabled) - theme choice
        // just won't persist across page loads.
      }
      syncButton();
    });

    syncButton();
  });

  // Photo gallery (About page): scroll-snap slider + <dialog> lightbox.
  document.addEventListener("DOMContentLoaded", function () {
    var gallery = document.querySelector("[data-gallery]");
    if (!gallery) {
      return;
    }

    var track = gallery.querySelector("[data-gallery-track]");
    var prevBtn = document.querySelector("[data-gallery-prev]");
    var nextBtn = document.querySelector("[data-gallery-next]");
    var triggers = Array.prototype.slice.call(
      track.querySelectorAll("[data-gallery-open]")
    );

    function updateNavState() {
      prevBtn.disabled = track.scrollLeft <= 1;
      nextBtn.disabled =
        track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
    }

    prevBtn.addEventListener("click", function () {
      track.scrollBy({ left: -track.clientWidth, behavior: "smooth" });
    });
    nextBtn.addEventListener("click", function () {
      track.scrollBy({ left: track.clientWidth, behavior: "smooth" });
    });
    track.addEventListener("scroll", updateNavState);
    window.addEventListener("resize", updateNavState);
    updateNavState();

    var dialog = document.querySelector("[data-lightbox]");
    if (!dialog || typeof dialog.showModal !== "function") {
      return;
    }

    var slides = Array.prototype.slice.call(
      dialog.querySelectorAll("[data-lightbox-slide]")
    );
    var countEl = dialog.querySelector("[data-lightbox-count]");
    var currentIndex = 0;
    var lastTrigger = null;

    function showSlide(index) {
      currentIndex = (index + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        slide.hidden = i !== currentIndex;
      });
      if (countEl) {
        countEl.textContent = currentIndex + 1 + " / " + slides.length;
      }
    }

    triggers.forEach(function (trigger, index) {
      trigger.addEventListener("click", function () {
        lastTrigger = trigger;
        showSlide(index);
        dialog.showModal();
      });
    });

    dialog.querySelector("[data-lightbox-prev]").addEventListener("click", function () {
      showSlide(currentIndex - 1);
    });
    dialog.querySelector("[data-lightbox-next]").addEventListener("click", function () {
      showSlide(currentIndex + 1);
    });
    dialog.querySelector("[data-lightbox-close]").addEventListener("click", function () {
      dialog.close();
    });

    // Clicking the backdrop (or the dialog's own padding, outside its
    // content) also closes it - both land on the dialog element itself as
    // event.target, unlike clicks on its children.
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) {
        dialog.close();
      }
    });

    dialog.addEventListener("keydown", function (event) {
      if (event.key === "ArrowLeft") {
        showSlide(currentIndex - 1);
      } else if (event.key === "ArrowRight") {
        showSlide(currentIndex + 1);
      }
    });

    dialog.addEventListener("close", function () {
      if (lastTrigger) {
        lastTrigger.focus();
      }
    });
  });
})();
