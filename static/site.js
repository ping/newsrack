/*
Copyright (c) 2022 https://github.com/ping/

This software is released under the GNU General Public License v3.0
https://opensource.org/licenses/GPL-3.0
*/


/*
    To maintain compat with the Kindle browser
    this will be transpiled with babel to ES5

    Document what doesn't work in the Kindle browser:
    - `const elements = document.querySelectorAll("selector")`
        - `elements.forEach()` is undefined
        - `for (const e in elements)` is undefined
*/
(function () {
    if (document.body.classList.contains("nonkindle")) {
        // use "read" param as a shortcut to the latest epub reader
        const params = URLSearchParams && new URLSearchParams(document.location.search.substring(1));
        const slug = (params && params.get("read")) ? params.get("read") : undefined;
        if (slug) {
            const periodical = document.getElementById(slug);
            if (periodical) {
                const readerLink = periodical.querySelector("a.reader");
                if (readerLink && readerLink["href"]) {
                    window.location.href = readerLink["href"];
                } else {
                    periodical.focus();
                }
            }
        }
    }

    const searchInfo = document.getElementById("search-info");
    const searchSyntaxLink = searchInfo.querySelector("a")
    const searchTextField = document.getElementById("search-text");
    const searchButton = document.getElementById("search-button");
    searchTextField.disabled = true;
    searchButton.disabled = true;
    const searchForm = document.getElementById("search-form");
    const clearSearchTextButton = document.getElementById("search-text-clear-btn");

    // in miliseconds
    const units = {
        year: 24 * 60 * 60 * 1000 * 365,
        month: 24 * 60 * 60 * 1000 * 365 / 12,
        day: 24 * 60 * 60 * 1000,
        hour: 60 * 60 * 1000,
        minute: 60 * 1000,
        second: 1000
    };
    // supported keyCodes: enter=13, space=32
    const supportedKeyCodes = [13];

    const isKindleBrowser = typeof (Intl) === "undefined";
    let rtf = null;
    if (typeof (Intl) !== "undefined") {
        // the Kindle browser doesn't support Intl
        rtf = new Intl.RelativeTimeFormat("en", {numeric: "auto"});
    }

    function getRelativeTime(d1, d2) {
        d2 = (typeof d2 !== "undefined") ? d2 : new Date();
        const elapsed = d1 - d2;
        // "Math.abs" accounts for both "past" & "future" scenarios
        for (const u in units) {
            if (Math.abs(elapsed) > units[u] || u === "second") {
                const diff = Math.round(elapsed / units[u]);
                if (typeof (Intl) !== "undefined") {
                    return rtf.format(diff, u);
                }
                // manually construct format, for the Kindle browser
                let unit = u;
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

    function toggleDateDisplay(target, isRelative) {
        const publishedDate = new Date(parseInt(target.attributes["data-pub-date"].value));
        target.title = publishedDate.toLocaleString();
        if (isRelative) {
            target.innerHTML = "Published " + getRelativeTime(publishedDate);
        } else {
            target.innerHTML = "Published " + publishedDate.toLocaleString();
        }
    }

    function sortSearchTermsPositions(a, b) {
        // by position, earlier mark sorts first
        if (a[0] < b[0]) {
            return -1;
        }
        if (a[0] > b[0]) {
            return 1;
        }
        // same position, longer mark sorts first
        if (a[1] > b[1]) {
            return -1;
        }
        if (a[1] < b[1]) {
            return 1;
        }
        return 0;
    }

    function markSearchTerms(positions, originalString) {
        const padding = originalString.indexOf("<li>");
        let markedString = "";
        let cumu_pos = padding > -1 ? padding : 0;
        if (cumu_pos >= 0) {
            markedString += originalString.substring(0, cumu_pos);
        }
        const offset = padding > -1 ? padding : 0;
        for (let z = 0; z < positions.length; z++) {
            const pos = positions[z];
            markedString += originalString.substring(cumu_pos, pos[0] + offset);
            cumu_pos += (pos[0] + offset - cumu_pos);
            markedString += "<mark>" + originalString.substring(cumu_pos, cumu_pos + pos[1]) + "</mark>";
            cumu_pos += pos[1];
        }
        markedString += originalString.substring(cumu_pos);
        return markedString;
    }

    function isScrolledIntoView(ele) {
        const rect = ele.getBoundingClientRect();
        // Only completely visible elements return true:
        return (rect.top >= 0) && (rect.bottom <= window.innerHeight);
        // Partially visible elements return true:
        // return rect.top < window.innerHeight && rect.bottom >= 0;
    }

    const refreshedDateEles = document.querySelectorAll("[data-refreshed-date]");
    for (let i = 0; i < refreshedDateEles.length; i++) {
        const refreshedDateEle = refreshedDateEles[i];
        const refreshedDate = new Date(parseInt(refreshedDateEle.attributes["data-refreshed-date"].value));
        refreshedDateEle.title = refreshedDate.toLocaleString();
        refreshedDateEle.innerHTML = getRelativeTime(refreshedDate);
    }

    // toggle pub date display
    const pudDateElements = document.querySelectorAll("[data-pub-date]");
    for (let i = 0; i < pudDateElements.length; i++) {
        const pubDateEle = pudDateElements[i];
        toggleDateDisplay(pubDateEle, true);

        pubDateEle.addEventListener("pointerenter", function (event) {
            toggleDateDisplay(event.target, false);
            const tags = event.target.parentElement.querySelector(".tags");
            if (tags) {
                tags.classList.add("hide");
            }
        }, false);

        pubDateEle.addEventListener("pointerleave", function (event) {
            toggleDateDisplay(event.target, true);
            const tags = event.target.parentElement.querySelector(".tags");
            if (tags) {
                tags.classList.remove("hide");
            }
        }, false);
    }

    // toggle collapsible toc for publication
    function pubdateActivate(e) {
        if (e.type === "keyup" && supportedKeyCodes.indexOf(e.keyCode || e.which) < 0) {     // not enter key
            return;
        }
        if (!isKindleBrowser && !this.classList.contains("is-open")) {
            // don't do this for the Kindle browser, because scrollIntoView doesn't seem to work
            // opening periodical
            const openedPeriodicals = document.querySelectorAll(".pub-date.is-open");
            for (let j = 0; j < openedPeriodicals.length; j++) {
                // close other opened periodicals
                const openedPeriodical = openedPeriodicals[j];
                openedPeriodical.classList.remove("is-open");
                openedPeriodical.parentElement.parentElement.querySelector(".contents").classList.add("hide");  // content
            }
        }
        const contents = this.parentElement.parentElement.querySelector(".contents");
        this.classList.toggle("is-open");
        contents.classList.toggle("hide");   // content
        const publication_id = this.parentElement.dataset["pubId"];
        if (contents.childElementCount <= 0 && RECIPE_DESCRIPTIONS[publication_id] !== undefined) {
            if (RECIPE_COVERS[publication_id] !== undefined) {
                contents.innerHTML = '<p class="cover">'
                    + '<a href="' + RECIPE_COVERS[publication_id]["cover"] + '">'
                    + '<img alt="Cover" src="'
                    + RECIPE_COVERS[publication_id]["thumbnail"] + '"></a></p>';
            }
            contents.innerHTML += RECIPE_DESCRIPTIONS[publication_id];
        }
        try {
            // scroll into element into view in case closing off another
            // content listing causes current periodical to go off-screen
            // don't do this for the Kindle browser, because scrollIntoView doesn't seem to work
            if (!isKindleBrowser && !isScrolledIntoView(this)) {
                this.parentElement.scrollIntoView();
            }
        } catch (e) {
            console.error(e);
        }
    }
    const accordionBtns = document.querySelectorAll(".pub-date");
    for (let i = 0; i < accordionBtns.length; i++) {
        const accordion = accordionBtns[i];
        accordion.addEventListener("click", pubdateActivate);
        accordion.addEventListener("keyup", pubdateActivate);
    }

    // toggle publications listing for category
    function categoryActivate(e) {
        if (e.type === "keyup" && supportedKeyCodes.indexOf(e.keyCode || e.which) < 0) {     // not enter key
            return;
        }
        if (e.target.nodeName.toLowerCase() === "a") {
            // don't do toggle action if it's a link
            return;
        }
        this.parentElement.classList.toggle("is-open");
        this.nextElementSibling.classList.toggle("hide");   // content
    }
    const categoryButtons = document.querySelectorAll("h2.category");
    for (let i = 0; i < categoryButtons.length; i++) {
        const category = categoryButtons[i];
        category.addEventListener("click", categoryActivate);
        category.addEventListener("keyup", categoryActivate);
    }

    // tag search shortcuts
    function tagActivate(e) {
        if (e.type === "keyup" && supportedKeyCodes.indexOf(e.keyCode || e.which) < 0) {     // not enter key
            return;
        }
        e.preventDefault();
        const tagSearchQuery = "tags:"+ e.target.innerText.substring(1);
        const currSearchQuery = searchTextField.value.trim();
        if (currSearchQuery.indexOf(tagSearchQuery) < 0) {
            searchTextField.value = currSearchQuery + (currSearchQuery === "" ? "" : " ") + tagSearchQuery;
        }
        searchTextField.focus();
    }
    const tagShortcuts = document.querySelectorAll(".tags .tag");
    for (let i = 0; i < tagShortcuts.length; i++) {
        const tag = tagShortcuts[i];
        tag.addEventListener("click", tagActivate);
        tag.addEventListener("keyup", tagActivate);
    }

    function catCloseActivate(e) {
        if (e.type === "keyup" && supportedKeyCodes.indexOf(e.keyCode || e.which) < 0) {     // not enter key
            return;
        }
        e.preventDefault();
        const cat = document.getElementById(e.target.dataset["clickTarget"]);
        cat.parentElement.classList.toggle("is-open");
        cat.nextElementSibling.classList.toggle("hide");    // content
        if (!cat.parentElement.classList.contains("is-open")) {
            cat.parentElement.scrollIntoView();
       }
    }
    const catCloseShortcuts = document.querySelectorAll("[data-click-target]");
    for (let i = 0; i < catCloseShortcuts.length; i++) {
        const shortcut = catCloseShortcuts[i];
        shortcut.addEventListener("click", catCloseActivate);
        shortcut.addEventListener("keyup", catCloseActivate);
    }

    window.addEventListener("DOMContentLoaded", function() {
        if (typeof(lunr) !== "undefined") {
            const readyPlaceholderText = searchTextField.getAttribute("data-placeholder");
            const periodicalsEles = document.querySelectorAll("ol.books > li");

            function resetSearch() {
                for (let i = 0; i < periodicalsEles.length; i++) {
                    const periodical = periodicalsEles[i];
                    periodical.classList.remove("hide");
                    const pubDate = periodical.querySelector(".pub-date");
                    if (pubDate) {
                        pubDate.classList.remove("is-open");
                    }
                    const contents = periodical.querySelector(".contents");
                    if (contents) {
                        contents.classList.add("hide");
                    }
                }
            }

            searchForm.onreset = function (event) {
                clearSearchTextButton.classList.add("hide");
                resetSearch();
            };
            searchTextField.onblur = function (event) {
                if (searchTextField.value.length === 0) {
                    clearSearchTextButton.classList.add("hide");
                } else {
                    clearSearchTextButton.classList.remove("hide");
                }
            };

            let idx = null;
            function handler() {
                if (this.readyState === XMLHttpRequest.DONE) {
                    const status = this.status;
                    if (status === 0 || (status >= 200 && status < 400)) {
                        idx = lunr.Index.load(JSON.parse(this.responseText));
                        searchButton.disabled = false;
                        searchTextField.placeholder = readyPlaceholderText;
                        searchTextField.disabled = false;
                        searchTextField.focus();
                    } else {
                        searchTextField.placeholder = "Unable to load search index: " + this.statusText;
                        console.error("Unable to load search index");
                        console.error(this);
                    }
                }
            }
            const httpRequest = new XMLHttpRequest();
            httpRequest.onreadystatechange = handler;
            httpRequest.open("GET", "lunr.json", true);
            httpRequest.send();

            // unhide everything when search field is cleared
            searchTextField.onchange = function(e) {
                if (this.value.trim().length > 0) {
                    return;
                }
                searchInfo.innerText = "";
                searchInfo.appendChild(searchSyntaxLink);
                resetSearch();
            };

            // search form submitted
            searchForm.onsubmit = function (e) {
                e.preventDefault();
                searchInfo.innerText = "";
                searchInfo.classList.add("error");
                const searchText = searchTextField.value.trim();
                if (searchText.length < 3) {
                    // this makes it work in the Kindle browser
                    searchInfo.appendChild(searchSyntaxLink);
                    searchInfo.innerHTML += "Search text must be at least 3 characters long.";
                    return;
                }

                try {
                    const results = idx.search(searchText);
                    if (results.length <= 0) {
                        searchInfo.appendChild(searchSyntaxLink);
                        searchInfo.innerHTML += "No results.";
                        resetSearch();
                        return;
                    }
                    searchInfo.appendChild(searchSyntaxLink);
                    const bookIds = [];
                    const resultsSumm = {};
                    for (let i = 0; i < results.length; i++) {
                        bookIds.push(results[i].ref);
                        const fields = [];
                        const metadata = results[i].matchData.metadata;
                        let resultPositions = {};
                        for (const key in metadata) {   // term
                            for (const kkey in metadata[key]) {     // field
                                if (!resultPositions[kkey]) {
                                    resultPositions[kkey] = [];
                                }
                                const positions = metadata[key][kkey]["position"] || [];
                                for (let z = 0; z < positions.length; z++) {
                                    resultPositions[kkey].push(positions[z]);
                                }
                                // sort enables multi-terms search to be properly marked
                                resultPositions[kkey].sort(sortSearchTermsPositions);
                            }
                        }
                        resultsSumm[results[i].ref] = resultPositions;

                    }
                    for (let i = 0; i < periodicalsEles.length; i++) {
                        const periodical = periodicalsEles[i];
                        const id = periodical["id"];
                        const contentsEle = periodical.querySelector(".contents");
                        const titleEle = periodical.querySelector(".title");

                        if (contentsEle && contentsEle.innerHTML !== "") {
                            contentsEle.innerHTML = RECIPE_DESCRIPTIONS[id];
                        }
                        if (titleEle) {
                            if (!titleEle.dataset["original"]) {
                                titleEle.dataset["original"] = titleEle.innerHTML;
                            }
                            // reset title ele
                            if (titleEle.innerHTML !== titleEle.dataset["original"]) {
                                titleEle.innerHTML = titleEle.dataset["original"];
                            }
                        }

                        if (bookIds.indexOf(id) < 0) {
                            periodical.classList.add("hide");
                            continue;
                        }
                        periodical.classList.remove("hide");
                        const cat = document.getElementById(periodical.dataset["catId"]);
                        if (cat) {
                            if (!cat.classList.contains("is-open")) {
                                cat.classList.add("is-open");
                            }
                            if (cat.nextElementSibling.classList.contains("hide")) {
                                cat.nextElementSibling.classList.remove("hide");
                            }
                        }
                        const pubDateEle = periodical.querySelector(".pub-date");

                        if (resultsSumm[id]["articles"]) {
                            pubDateEle.classList.add("is-open");
                            if (contentsEle) {
                                contentsEle.classList.remove("hide");
                                const positions = resultsSumm[id]["articles"];
                                contentsEle.innerHTML = markSearchTerms(positions, RECIPE_DESCRIPTIONS[id]);
                            }
                        }
                        if (resultsSumm[id]["title"]) {
                            if (!resultsSumm[id]["articles"]) {
                                pubDateEle.classList.remove("is-open");
                                if (contentsEle) {
                                    contentsEle.classList.add("hide");
                                }
                            }
                            if (titleEle) {
                                const positions = resultsSumm[id]["title"] || [];
                                titleEle.innerHTML = markSearchTerms(positions, titleEle.innerHTML);
                            }
                        }
                    }
                } catch (e) {
                    searchInfo.appendChild(searchSyntaxLink);
                    searchInfo.innerHTML += e.name + ": " + e.message;
                }

            };
        }
    });

})();