document.addEventListener('DOMContentLoaded', function () {
    var userRoles = (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];
    var isClient  = userRoles.includes('Client');
    var isAdmin   = (frappe.boot && frappe.boot.user && frappe.boot.user.name) === 'Administrator';

    function hideElements(selector) {
        if (isAdmin) return;
        var intervalId = setInterval(function () {
            var elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                elements.forEach(function (el) {
                    el.style.display = 'none';
                });
                clearInterval(intervalId);
            }
        }, 5);
    }

    // Hide workspace edit/create buttons for all non-admin users
    var selectors = [
        'button[data-label="Edit"]',
        'button[data-label="Create%20Workspace"]'
    ];
    selectors.forEach(hideElements);

    // Disable awesome bar (search bar) for Client role users
    if (isClient) {
        hideElements('.search-bar');

        // Also prevent keyboard shortcut Ctrl+/ or Ctrl+G from opening the bar
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === '/' || e.key === 'g' || e.key === 'G')) {
                e.stopImmediatePropagation();
                e.preventDefault();
            }
        }, true);
    }
});