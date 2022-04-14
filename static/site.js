(function() {
    // in miliseconds
    var units = {
      year  : 24 * 60 * 60 * 1000 * 365,
      month : 24 * 60 * 60 * 1000 * 365/12,
      day   : 24 * 60 * 60 * 1000,
      hour  : 60 * 60 * 1000,
      minute: 60 * 1000,
      second: 1000
    };

    var rtf = null;
    if (typeof(Intl) !== "undefined") {
        rtf = new Intl.RelativeTimeFormat("en", {numeric: "auto"});
    }

    function getRelativeTime(d1, d2) {
        d2 = (typeof d2 !== "undefined") ? d2 : new Date();
        var elapsed = d1 - d2;
        // "Math.abs" accounts for both "past" & "future" scenarios
        for (var u in units) {
            if (Math.abs(elapsed) > units[u] || u === "second") {
                var diff = Math.round(elapsed / units[u]);
                if (typeof(Intl) !== "undefined") {
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

    var pudDateElements = document.querySelectorAll("[data-pub-date]");
    for (var i = 0; i < pudDateElements.length; i++) {
        var pubDateEle = pudDateElements[i];
        var publishedDate = new Date(parseInt(pubDateEle.attributes["data-pub-date"].value));
        pubDateEle.title = publishedDate.toLocaleString();
        pubDateEle.innerHTML = "Published " + getRelativeTime(publishedDate);
    }

})();