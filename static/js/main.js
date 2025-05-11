
document.addEventListener("DOMContentLoaded", function () {
  try {
    // Force sidebar layout class if it's missing
    const body = document.body;
    if (!body.classList.contains("g-sidenav-show")) {
      body.classList.add("g-sidenav-show");
    }

    // Re-initialize sidebar if necessary
    if (typeof sidenav === "function") {
      sidenav.init();
    }
  } catch (e) {
    console.warn("Material Dashboard JS initialization failed:", e);
  }
});
