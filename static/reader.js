(function () {
    const params = URLSearchParams && new URLSearchParams(document.location.search.substring(1));
    const file = params && params.get("file") && decodeURIComponent(params.get("file"));
    const currentSectionIndex = (params && params.get("loc")) ? params.get("loc") : undefined;
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
    errEle.classList.add("m-5");

    if (!isValidBook) {
        errEle.innerText = "Remote books not allowed.";
        loadingContainer.innerHTML = "";
        loadingContainer.append(errEle);
    } else {
        const book = ePub(file);
        const rendition = book.renderTo(
            "epub-viewer",
            {width: "100%", height: "100%", snap: true, manager: "continuous"}
        );
        rendition.display(currentSectionIndex);
        book.on("openFailed", function (e) {
            console.error(e);
            errEle.innerText = e.toString();
            loadingContainer.innerHTML = "";
            loadingContainer.append(errEle);
        });

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

            const keyListener = function (e) {
                // Left Key
                if ((e.keyCode || e.which) === 37) {
                    book.package.metadata.direction === "rtl" ? rendition.next() : rendition.prev();
                }
                // Right Key
                if ((e.keyCode || e.which) === 39) {
                    book.package.metadata.direction === "rtl" ? rendition.prev() : rendition.next();
                }
            };
            rendition.on("keyup", keyListener);
            document.addEventListener("keyup", keyListener, false);
        });

        window.addEventListener("unload", function () {
            this.book.destroy();
        });

        book.loaded.navigation.then(function (toc) {
            const $select = document.getElementById("toc");
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

            $select.appendChild(docfrag);

            $select.onchange = function () {
                const index = $select.selectedIndex;
                const url = $select.options[index].getAttribute("ref");
                rendition.display(url);
                return false;
            };

        });

        book.loaded.metadata.then(function (meta) {
            document.title = meta.title;
        });

        rendition.on("relocated", function (location) {
            const $select = document.getElementById("toc");
            const $selected = $select.querySelector("option[selected]");
            if ($selected) {
                $selected.removeAttribute("selected");
            }

            const $options = $select.querySelectorAll("option");
            for (let i = 0; i < $options.length; ++i) {
                let selected = $options[i].getAttribute("ref") === location.start.href;
                if (selected) {
                    $options[i].setAttribute("selected", "");
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

        });

        rendition.themes.register("viewer-theme", "viewer-theme.css");
        rendition.themes.select("viewer-theme");

        window.book = book;
    }

})();
