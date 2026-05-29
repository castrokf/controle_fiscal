(() => {
  const body = document.body;
  const toggle = document.querySelector("[data-sidebar-toggle]");
  const closeTargets = document.querySelectorAll("[data-sidebar-close], .sidebar .nav-link");

  const closeSidebar = () => {
    body.classList.remove("sidebar-open");
    toggle?.setAttribute("aria-expanded", "false");
  };

  toggle?.addEventListener("click", () => {
    const isOpen = body.classList.toggle("sidebar-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  closeTargets.forEach((target) => {
    target.addEventListener("click", () => {
      if (window.matchMedia("(max-width: 1024px)").matches) {
        closeSidebar();
      }
    });
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSidebar();
    }
  });
})();
