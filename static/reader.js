/*
Copyright (c) 2023 https://github.com/ping/

This software is released under the GNU General Public License v3.0
https://opensource.org/licenses/GPL-3.0
*/

(function () {
    const params = URLSearchParams && new URLSearchParams(document.location.search.substring(1));
    const file = (params && params.get("file")) ? params.get("file") : undefined;
    const hashParams = URLSearchParams && new URLSearchParams(document.location.hash.substring(1));
    const titleId = (params && params.get("id")) ? params.get("id") : "";
    const cookieKey = "title_" + titleId;
    const currentSectionIndex = (hashParams && hashParams.get("loc")) ? hashParams.get("loc") : JSON.parse(Cookies.get(cookieKey) || "{}")[file];
    let isValidBook;
    try {
        new URL(file);
        isValidBook = false;
    } catch (e) {
        isValidBook = true;
    }
    const loadingContainer = document.getElementById("loading-container");
    const displayContainer = document.getElementById("display-container");
    const errEle = document.createElement("span");
    errEle.classList.add("m-5", "d-block");
    const backLink = document.createElement("a");
    backLink["href"] = "./";
    backLink.innerHTML = '<svg><use href="reader_sprites.svg#icon-home"></use></svg> Back to Home';
    backLink.classList.add("d-flex", "align-items-center", "my-1", "gap-1", "justify-content-center");

    if (!isValidBook) {
        errEle.innerText = "Remote books not allowed.";
        errEle.append(backLink);
        loadingContainer.innerHTML = "";
        loadingContainer.append(errEle);
        return;
    }

    const book = ePub(file);
    const rendition = book.renderTo(
        "epub-viewer",
        {width: "100%", height: "100%", snap: true, manager: "continuous"}
    );
    rendition.display(currentSectionIndex);

    book.on("openFailed", function (e) {
        console.error(e);
        errEle.innerText = e.toString();
        errEle.append(backLink);
        loadingContainer.innerHTML = "";
        loadingContainer.append(errEle);
    });

    function gotoNextChapter() {
        const nextIndex = book.package.metadata.direction === "rtl" ? rendition.location.end.index - 1 : rendition.location.end.index + 1;
        if (nextIndex >= 0 && nextIndex < rendition.book.spine.spineItems.length) {
            rendition.display(rendition.book.spine.spineItems[nextIndex]["href"]);
        }
    }

    function gotoPrevChapter() {
        const prevIndex = book.package.metadata.direction === "rtl" ? rendition.location.start.index + 1 : rendition.location.start.index - 1;
        if (prevIndex >= 0 && prevIndex < rendition.book.spine.spineItems.length) {
            rendition.display(rendition.book.spine.spineItems[prevIndex]["href"]);
        }
    }

    book.ready.then(function () {
        if (loadingContainer) {
            loadingContainer.remove();
        }
        displayContainer.classList.remove("d-none");
        const next = document.getElementById("next");
        next.addEventListener("click", function (e) {
            book.package.metadata.direction === "rtl" ? rendition.prev() : rendition.next();
            e.preventDefault();
        }, false);

        const prev = document.getElementById("prev");
        prev.addEventListener("click", function (e) {
            book.package.metadata.direction === "rtl" ? rendition.next() : rendition.prev();
            e.preventDefault();
        }, false);

        const nextChapter = document.getElementById("next-chapter");
        nextChapter.addEventListener("click", function (e) {
            e.preventDefault();
            gotoNextChapter();
        }, false);

        const prevChapter = document.getElementById("prev-chapter");
        prevChapter.addEventListener("click", function (e) {
            e.preventDefault();
            gotoPrevChapter();
        }, false);

        const keyListener = function (e) {
            // Left Key
            if ((e.keyCode || e.which) === 37) {
                book.package.metadata.direction === "rtl" ? rendition.next() : rendition.prev();
            }
            // Right Key
            if ((e.keyCode || e.which) === 39) {
                book.package.metadata.direction === "rtl" ? rendition.prev() : rendition.next();
            }
            // Up key
            if ((e.keyCode || e.which) === 38) {
                gotoPrevChapter();
            }
            // Down key
            if ((e.keyCode || e.which) === 40) {
                gotoNextChapter();
            }
            // "t" key
            if ((e.keyCode || e.which) === 84) {
                document.getElementById("toc").focus();
            }
        };
        rendition.on("keyup", keyListener);
        document.addEventListener("keyup", keyListener, false);
    });

    book.loaded.navigation.then(function (toc) {
        const tocSelect = document.getElementById("toc");
        const docfrag = document.createDocumentFragment();

        toc.forEach(function (chapter) {
            const option = document.createElement("option");
            option.textContent = chapter.label;
            option.setAttribute("ref", chapter.href);
            docfrag.appendChild(option);
            chapter.subitems.forEach(function (subitem) {
                const subOption = document.createElement("option");
                subOption.textContent = "* " + subitem.label;
                subOption.setAttribute("ref", subitem.href);
                docfrag.appendChild(subOption);
                subitem.subitems.forEach(function (sub2item) {
                    const sub2Option = document.createElement("option");
                    sub2Option.textContent = "--- " + sub2item.label;
                    sub2Option.setAttribute("ref", sub2item.href);
                    docfrag.appendChild(sub2Option);
                });
            });
        });

        tocSelect.appendChild(docfrag);

        tocSelect.onchange = function () {
            const index = tocSelect.selectedIndex;
            const url = tocSelect.options[index].getAttribute("ref");
            rendition.display(url);
            return false;
        };

    });

    book.loaded.metadata.then(function (meta) {
        document.title = meta.title;
        document.getElementById("epub-title").innerText = meta.title;
    });

    rendition.on("relocated", function (location) {

        const tocSelect = document.getElementById("toc");
        const selectedOption = tocSelect.querySelector("option[selected]");
        if (selectedOption) {
            selectedOption.removeAttribute("selected");
        }

        const options = tocSelect.querySelectorAll("option");
        for (let i = 0; i < options.length; ++i) {
            let selected = options[i].getAttribute("ref") === location.start.href;
            if (selected) {
                options[i].setAttribute("selected", "");
            }
        }

        const next = book.package.metadata.direction === "rtl" ? document.getElementById("prev") : document.getElementById("next");
        const prev = book.package.metadata.direction === "rtl" ? document.getElementById("next") : document.getElementById("prev");

        if (location.atEnd) {
            next.classList.add("invisible");
        } else {
            next.classList.remove("invisible");
        }

        if (location.atStart) {
            prev.classList.add("invisible");
        } else {
            prev.classList.remove("invisible");
        }

        const nextChapter = book.package.metadata.direction === "rtl" ? document.getElementById("prev-chapter") : document.getElementById("next-chapter");
        const prevChapter = book.package.metadata.direction === "rtl" ? document.getElementById("next-chapter") : document.getElementById("prev-chapter");

        if (location.start.index <= 0 || location.start.index <= 0) {
            prevChapter.classList.add("invisible");
        } else {
            prevChapter.classList.remove("invisible");
        }

        const maxIndex = book.spine.spineItems.length - 1;
        if (location.start.index >= maxIndex || location.start.index >= maxIndex) {
            nextChapter.classList.add("invisible");
        } else {
            nextChapter.classList.remove("invisible");
        }

        const cfi = location.start.cfi;
        const hashParams = URLSearchParams && new URLSearchParams(document.location.hash.substring(1));
        hashParams.set("loc", cfi);
        document.location.replace("#" + hashParams.toString());
        let progress = {};
        progress[file] = cfi;
        Cookies.set(cookieKey, JSON.stringify(progress), { path: "", expires: 30 });
    });

    rendition.themes.register(
        "viewer-theme",
        document.documentElement.getAttribute('data-theme') === "light" ?
            "viewer-theme-light.css" : "viewer-theme-dark.css"
    );
    rendition.themes.select("viewer-theme");

    window.book = book;
    window.addEventListener("unload", function () {
        this.book.destroy();
    });

})();
