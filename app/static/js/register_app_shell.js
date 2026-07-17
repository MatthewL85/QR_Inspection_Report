(function () {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/app-shell-sw.js", { scope: "/" }).catch(function () {
      // App shell registration must never block login, dashboards or governed workflows.
    });
  });
})();
