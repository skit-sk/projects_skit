/**
 * TradeHelp — TV Widgets helpers
 * Each widget page loads embed-widget-*.js via <script async>.
 * This file provides shared helpers.
 */
(function () {
    // helper: refresh all embeds on a page
    function refreshEmbeds() {
        document.querySelectorAll('script[src*="tradingview"]').forEach(s => {
            // re-append to force reload
            const ns = document.createElement('script');
            ns.type = s.type;
            ns.textContent = s.textContent;
            ns.async = true;
            const parent = s.parentNode;
            parent.removeChild(s);
            parent.appendChild(ns);
        });
    }

    // helper: open fullscreen
    function fullscreen(el) {
        if (el.requestFullscreen) el.requestFullscreen();
        else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    }

    window.tvHelpers = { refreshEmbeds, fullscreen };
})();
