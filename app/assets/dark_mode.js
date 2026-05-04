// NZ Habitat Intelligence — Dark Mode Toggle

// Clientside callback to toggle dark mode on body element
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.dark_mode = {
    toggle_body_class: function(n_clicks, current_class) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        var body = document.body;
        if (body.classList.contains('dark-mode')) {
            body.classList.remove('dark-mode');
        } else {
            body.classList.add('dark-mode');
        }
        return window.dash_clientside.no_update;
    }
};
