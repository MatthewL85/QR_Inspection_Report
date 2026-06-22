
document.addEventListener("DOMContentLoaded", function () {
  try {
    const body = document.body;
    if (!body.classList.contains("g-sidenav-show")) {
      body.classList.add("g-sidenav-show");
    }

    const enforceDesktopSidebar = function () {
      if (window.matchMedia("(min-width: 768px)").matches) {
        body.classList.remove("g-sidenav-hidden", "sidebar-open");
        body.classList.add("g-sidenav-pinned");
      } else {
        body.classList.remove("g-sidenav-pinned");
      }
    };

    enforceDesktopSidebar();
    window.addEventListener("resize", enforceDesktopSidebar);

    if (typeof sidenav === "function") {
      sidenav.init();
    }
  } catch (e) {
    console.warn("Material Dashboard JS initialization failed:", e);
  }
});
