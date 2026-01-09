// Owner Dashboard JS
document.addEventListener('DOMContentLoaded', () => {
    // Check Theme
    if (localStorage.getItem('theme') === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark'); // Ensure it's off if preference is light or default
    }
    console.log('Owner Dashboard Loaded');

    // Sidebar Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarClose = document.getElementById('sidebar-close');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const navLinks = document.querySelectorAll('.sidebar-link');
    const currentPath = window.location.pathname;

    // Functions
    const openSidebar = () => {
        sidebar.classList.remove('-translate-x-full');
        sidebarOverlay.classList.remove('hidden', 'opacity-0');
    };

    const closeSidebar = () => {
        sidebar.classList.add('-translate-x-full');
        sidebarOverlay.classList.add('hidden', 'opacity-0');
    };

    // Event Listeners
    if (sidebarToggle) sidebarToggle.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);


    // Link Active State & Mobile Auto-Close
    navLinks.forEach(link => {
        // Set active state on load
        if(link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
        
        link.addEventListener('click', () => {
             // Update active state
             navLinks.forEach(l => l.classList.remove('active'));
             link.classList.add('active');

             // Close sidebar on mobile when a link is clicked
             if (window.innerWidth < 768) { // md breakpoint
                 closeSidebar();
             }
        });
    });
});
