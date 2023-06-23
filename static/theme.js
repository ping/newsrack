/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2023 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
    'use strict'

    // supported keyCodes: enter=13, space=32
    const supportedKeyCodes = [13];
    const getStoredTheme = () => localStorage.getItem('theme');
    const setStoredTheme = theme => localStorage.setItem('theme', theme);

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) {
            return storedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const getCurrTheme = () => {
        return document.documentElement.getAttribute('data-theme');
    };

    const setTheme = theme => {
        if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    };

    setTheme(getPreferredTheme());

    const showActiveTheme = (theme) => {
        const themeIcon = document.querySelector('#toggle-theme-icon use');
        if (!themeIcon) {
            return
        }
        let icon = 'auto';
        if (theme === 'dark') { icon = 'light'; }
        if (theme === 'light') { icon = 'dark'; }
        themeIcon.setAttribute('href', `reader_sprites.svg#icon-theme-${icon}`);
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme();
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme());
        }
    });

    const toggleTheme = (e) => {
        if (e.type === "keyup" && supportedKeyCodes.indexOf(e.keyCode || e.which) < 0) {     // not enter key
            return;
        }
        const newTheme = getCurrTheme() === 'dark' ? 'light' : 'dark';
        setStoredTheme(newTheme);
        setTheme(newTheme);
        const themeSvg = document.getElementById('toggle-theme-icon');
        themeSvg.addEventListener("animationend", (e) => {
            e.target.classList.remove("spin-it");
            showActiveTheme(newTheme);
        });
        themeSvg.classList.add("spin-it");
    };

    window.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme());

        const themeToggler = document.getElementById("toggle-theme");
        if (themeToggler) {
            themeToggler.addEventListener("click", toggleTheme);
            themeToggler.addEventListener("keyup", toggleTheme);
        }
    });
})();