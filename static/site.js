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

    const searchInfo = document.getElementById("search-info");
    const searchTextField = document.getElementById("search-text");
    const searchButton = document.getElementById("search-button");
    searchTextField.disabled = true;
    searchButton.disabled = true;

    // in miliseconds
    const units = {
        year: 24 * 60 * 60 * 1000 * 365,
        month: 24 * 60 * 60 * 1000 * 365 / 12,
        day: 24 * 60 * 60 * 1000,
        hour: 60 * 60 * 1000,
        minute: 60 * 1000,
        second: 1000
    };

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
        let tags = "";
        if (typeof(target.parentElement.dataset["tags"]) !== "undefined"
            && target.parentElement.dataset["tags"].trim().length > 0) {
            tags = " " + '<span class="tags">' + target.parentElement.dataset["tags"] + "</span>";
        }
        target.title = publishedDate.toLocaleString();
        if (isRelative) {
            target.innerHTML = "Published " + getRelativeTime(publishedDate) + tags;
        } else {
            target.innerHTML = "Published " + publishedDate.toLocaleString() + tags;
        }
    }

    function isScrolledIntoView(ele) {
        const rect = ele.getBoundingClientRect();
        // Only completely visible elements return true:
        return (rect.top >= 0) && (rect.bottom <= window.innerHeight);
        // Partially visible elements return true:
        // return rect.top < window.innerHeight && rect.bottom >= 0;
    }

    const refreshedDateEle = document.getElementById("refreshed_dt");
    const refreshedDate = new Date(parseInt(refreshedDateEle.attributes["data-refreshed-date"].value));
    refreshedDateEle.title = refreshedDate.toLocaleString();
    refreshedDateEle.innerHTML = getRelativeTime(refreshedDate);

    // toggle pub date display
    const pudDateElements = document.querySelectorAll("[data-pub-date]");
    for (let i = 0; i < pudDateElements.length; i++) {
        const pubDateEle = pudDateElements[i];
        toggleDateDisplay(pubDateEle, true);

        pubDateEle.addEventListener("pointerenter", function (event) {
            toggleDateDisplay(event.target, false);
        }, false);

        pubDateEle.addEventListener("pointerleave", function (event) {
            toggleDateDisplay(event.target, true);
        }, false);
    }

    // toggle collapsible toc for publication
    const accordionBtns = document.querySelectorAll(".pub-date");
    for (let i = 0; i < accordionBtns.length; i++) {
        const accordion = accordionBtns[i];
        accordion.onclick = function () {
            if (!isKindleBrowser && !this.classList.contains("is-open")) {
                // don't do this for the Kindle browser, because scrollIntoView doesn't seem to work
                // opening periodical
                const openedPeriodicals = document.querySelectorAll(".pub-date.is-open");
                for (let j = 0; j < openedPeriodicals.length; j++) {
                    // close other opened periodicals
                    const openedPeriodical = openedPeriodicals[j];
                    openedPeriodical.classList.remove("is-open");
                    openedPeriodical.nextElementSibling.classList.add("hide");  // content
                }
            }
            this.classList.toggle("is-open");
            this.nextElementSibling.classList.toggle("hide");   // content
            const slug = this.parentElement.id;
            if (this.nextElementSibling.childElementCount <= 0 && RECIPE_DESCRIPTIONS[slug] !== undefined) {
                if (RECIPE_COVERS[slug] !== undefined) {
                    this.nextElementSibling.innerHTML = '<p class="cover">'
                        + '<a href="' + RECIPE_COVERS[slug]["cover"] + '">'
                        + '<img alt="Cover" src="'
                        + RECIPE_COVERS[slug]["thumbnail"] + '"></a></p>';
                }
                this.nextElementSibling.innerHTML += RECIPE_DESCRIPTIONS[slug];
            }
            try {
                // scroll into element into view in case closing off another
                // content listing causes current periodical to go off-screen
                // don't do this for the Kindle browser, because scrollIntoView doesn't seem to work
                if (!isKindleBrowser && !isScrolledIntoView(this.parentElement)) {
                    this.parentElement.scrollIntoView();
                }
            } catch (e) {
                console.error(e);
            }
        };
    }

    // toggle publications listing for category
    const categoryButtons = document.querySelectorAll("h2.category");
    for (let i = 0; i < categoryButtons.length; i++) {
        const category = categoryButtons[i];
        category.onclick = function (e) {
            if (e.target.nodeName.toLowerCase() === "a") {
                // don't do toggle action if it's a link
                return;
            }
            this.parentElement.classList.toggle("is-open");
            this.nextElementSibling.classList.toggle("hide");   // content
        };
    }

    const catCloseShortcuts = document.querySelectorAll("[data-click-target]");
    for (let i = 0; i < catCloseShortcuts.length; i++) {
        const shortcut = catCloseShortcuts[i];
        shortcut.onclick = function (e) {
            e.preventDefault();
            const cat = document.getElementById(e.target.dataset["clickTarget"]);
            cat.parentElement.classList.toggle("is-open");
            cat.nextElementSibling.classList.toggle("hide");    // content
            if (!cat.parentElement.classList.contains("is-open")) {
                cat.parentElement.scrollIntoView();
           }
        };
    }

    window.addEventListener("DOMContentLoaded", function() {
        if (typeof(lunr) !== "undefined") {
            const ogPlaceholderText = searchTextField.placeholder;
            searchTextField.placeholder = "Indexing search...";
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

            const idx = lunr(function () {
                this.field("title");
                this.field("articles");
                this.field("tags");
                this.field("category");

                for (let i = 0; i < periodicalsEles.length; i++) {
                    const periodical = periodicalsEles[i];
                    const id = periodical["id"];
                    const catName = periodical.dataset["catName"];
                    const title = periodical.querySelector(".title").textContent;
                    const contentTemp = document.createElement("div");
                    contentTemp.innerHTML = RECIPE_DESCRIPTIONS[id];
                    const articlesEles = contentTemp.querySelectorAll("ul > li");
                    const articles = [];
                    for (let j = 0; j < articlesEles.length; j++) {
                        const articleEle = articlesEles[j];
                        articles.push(articleEle.textContent);
                    }
                    this.add({
                        "id": id,
                        "title": title,
                        "articles": articles.join(" "),
                        "tags": periodical.dataset["tags"],
                        "category": catName
                    });
                }
                searchTextField.placeholder = ogPlaceholderText;
                searchTextField.disabled = false;
                searchButton.disabled = false;
            });

            // unhide everything when search field is cleared
            document.getElementById("search-text").onchange = function(e) {
                if (this.value.trim().length > 0) {
                    return;
                }
                searchInfo.innerText = "";
                resetSearch();
            };

            // search form submitted
            document.getElementById("search-form").onsubmit = function (e) {
                e.preventDefault();
                searchInfo.innerText = "";
                const searchText = document.getElementById("search-text").value.trim();
                if (searchText.length < 3) {
                    searchInfo.innerText = "Search text must be at least 3 characters long.";
                    return;
                }

                const results = idx.search(searchText);
                if (results.length <= 0) {
                    searchInfo.innerText = "No results.";
                    resetSearch();
                    return;
                }

                const bookIds = [];
                const resultsSumm = {};
                for (let i = 0; i < results.length; i++) {
                    bookIds.push(results[i].ref);
                    const fields = [];
                    const metadata = results[i].matchData.metadata;
                    for (const key in metadata) {
                        for (const kkey in metadata[key]) {
                            fields.push(kkey);
                        }
                    }
                    resultsSumm[results[i].ref] = fields;

                }
                for (let i = 0; i < periodicalsEles.length; i++) {
                    const periodical = periodicalsEles[i];
                    const id = periodical["id"];

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
                    const contentsEle = periodical.querySelector(".contents");
                    if (resultsSumm[id].indexOf("articles") >= 0) {
                        pubDateEle.classList.add("is-open");
                        if (contentsEle) {
                            contentsEle.classList.remove("hide");
                        }
                        contentsEle.classList.remove("hide");
                        if (contentsEle.innerHTML === "") {
                            contentsEle.innerHTML = RECIPE_DESCRIPTIONS[id];
                        }

                    } else {
                        pubDateEle.classList.remove("is-open");
                        if (contentsEle) {
                            contentsEle.classList.add("hide");
                        }
                    }
                }
            };
        }
    });

})();