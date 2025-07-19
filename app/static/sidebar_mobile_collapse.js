
document.addEventListener('DOMContentLoaded', function () {
  const toggleButton = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidenav-main');

  if (toggleButton && sidebar) {
    toggleButton.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed');
    });
  }
});
