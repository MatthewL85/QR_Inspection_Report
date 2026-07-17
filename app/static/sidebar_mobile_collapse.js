
document.addEventListener('DOMContentLoaded', function () {
  const toggleButton = document.getElementById('sidebarToggle');
  const topToggleButton = document.getElementById('sidebarToggleTop');
  const sidebar = document.getElementById('sidenav-main');
  const overlay = document.getElementById('sidebarOverlay');
  const isMobile = () => window.matchMedia('(max-width: 767.98px)').matches;

  function toggleSidebar() {
    if (!sidebar) return;

    if (isMobile()) {
      document.body.classList.toggle('sidebar-open');
      document.body.classList.remove('sidebar-collapsed');
      return;
    }

    sidebar.classList.toggle('collapsed');
    document.body.classList.toggle('sidebar-collapsed');
  }

  if (toggleButton && toggleButton.dataset.sidebarBound !== '1') {
    toggleButton.dataset.sidebarBound = '1';
    toggleButton.addEventListener('click', toggleSidebar);
  }

  if (topToggleButton && topToggleButton.dataset.sidebarBound !== '1') {
    topToggleButton.dataset.sidebarBound = '1';
    topToggleButton.addEventListener('click', toggleSidebar);
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      document.body.classList.remove('sidebar-open');
    });
  }
});
