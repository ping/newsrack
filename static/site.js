(function () {
    // in miliseconds
    var units = {
        year: 24 * 60 * 60 * 1000 * 365,
        month: 24 * 60 * 60 * 1000 * 365 / 12,
        day: 24 * 60 * 60 * 1000,
        hour: 60 * 60 * 1000,
        minute: 60 * 1000,
        second: 1000
    };

    var rtf = null;
    if (typeof (Intl) !== "undefined") {
        rtf = new Intl.RelativeTimeFormat("en", {numeric: "auto"});
    }

    function getRelativeTime(d1, d2) {
        d2 = (typeof d2 !== "undefined") ? d2 : new Date();
        var elapsed = d1 - d2;
        // "Math.abs" accounts for both "past" & "future" scenarios
        for (var u in units) {
            if (Math.abs(elapsed) > units[u] || u === "second") {
                var diff = Math.round(elapsed / units[u]);
                if (typeof (Intl) !== "undefined") {
                    return rtf.format(diff, u);
                }
                // manually construct format
                var unit = u;
                if (Math.abs(diff) > 1) {
                    unit = u + "s";
                }
                if (diff < 0) {
                    return Math.abs(diff) + " " + unit + " ago"
                } else {
                    return "in " + diff + " " + unit;
                }
            }
        }
    }

    var refreshedDateEle = document.getElementById("refreshed_dt");
    var refreshedDate = new Date(parseInt(refreshedDateEle.attributes["data-refreshed-date"].value));
    refreshedDateEle.title = refreshedDate.toLocaleString();
    refreshedDateEle.innerHTML = getRelativeTime(refreshedDate);

    // toggle pub date display
    var pudDateElements = document.querySelectorAll("[data-pub-date]");
    for (var i = 0; i < pudDateElements.length; i++) {
        var pubDateEle = pudDateElements[i];
        var publishedDate = new Date(parseInt(pubDateEle.attributes["data-pub-date"].value));
        pubDateEle.title = publishedDate.toLocaleString();
        pubDateEle.innerHTML = "Published " + getRelativeTime(publishedDate);

        pubDateEle.addEventListener("pointerenter", function (event) {
            var publishedDate = new Date(parseInt(event.target.attributes["data-pub-date"].value));
            event.target.innerHTML = "Published " + publishedDate.toLocaleString();
        }, false);

        pubDateEle.addEventListener("pointerleave", function (event) {
            var publishedDate = new Date(parseInt(event.target.attributes["data-pub-date"].value));
            event.target.innerHTML = "Published " + getRelativeTime(publishedDate);
        }, false);
    }

    // toggle collapsible toc for publication
    var accordionBtns = document.querySelectorAll(".pub-date");
    for (var i = 0; i < accordionBtns.length; i++) {
        var accordion = accordionBtns[i];
        accordion.onclick = function () {
            this.classList.toggle("is-open");
            this.nextElementSibling.classList.toggle("hide");   // content
        };
    }

        // toggle collapsible toc for publication
    var categoryButtons = document.querySelectorAll("h2.category");
    for (var i = 0; i < categoryButtons.length; i++) {
        var category = categoryButtons[i];
        category.onclick = function () {
            this.classList.toggle("is-open");
            this.nextElementSibling.classList.toggle("hide");   // content
        };
    }

    var catCloseShortcuts = document.querySelectorAll("[data-click-target]");
    for (var i = 0; i < catCloseShortcuts.length; i++) {
        var shortcut = catCloseShortcuts[i];
        shortcut.onclick = function (e) {
            e.preventDefault();
            var cat = document.getElementById(e.target.dataset["clickTarget"]);
            cat.classList.toggle("is-open");
            cat.nextElementSibling.classList.toggle("hide");    // content
        };
    }

    // stupid workaround instead of relying on screen size
    // to increase font size for non-kindle devices
    if (navigator.userAgent.indexOf("Mozilla/5.0 (X11") < 0) {
        var cssEle = document.createElement("style");
        cssEle.innerText = "{nonkindle}";       // replaced by _generate.py
        document.head.appendChild(cssEle);
    }

})();