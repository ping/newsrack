# Copyright (c) 2022 https://github.com/ping/
#
# This software is released under the GNU General Public License v3.0
# https://opensource.org/licenses/GPL-3.0
import logging
import os.path
import re
import sys
import textwrap
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont  # type: ignore

from _recipe_utils import CoverOptions


class ExperimentalFunctionWarning(UserWarning):
    """Experimental features warning."""


# From django
def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
        value = re.sub(r"[^\w\s-]", "", value, flags=re.U).strip().lower()
        return re.sub(r"[-\s]+", "-", value, flags=re.U)
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def calc_resize(
    max_size: Tuple[int, int],
    curr_size: Tuple[int, int],
    min_size: Tuple[int, int] = (0, 0),
) -> Optional[Tuple[int, int]]:
    """
    Calculate if resize is required based on the max size desired
    and the current size
    :param max_size: tuple of (width, height)
    :param curr_size: tuple of (width, height)
    :param min_size: tuple of (width, height)
    :return:
    """
    max_width, max_height = max_size or (0, 0)
    min_width, min_height = min_size or (0, 0)

    if (max_width and min_width > max_width) or (
        max_height and min_height > max_height
    ):
        raise ValueError("Invalid min / max sizes.")

    orig_width, orig_height = curr_size
    if (
        max_width
        and max_height
        and (orig_width > max_width or orig_height > max_height)
    ):
        resize_factor = min(
            1.0 * max_width / orig_width, 1.0 * max_height / orig_height
        )
        new_width = int(resize_factor * orig_width)
        new_height = int(resize_factor * orig_height)
        return new_width, new_height

    elif (
        min_width
        and min_height
        and (orig_width < min_width or orig_height < min_height)
    ):
        resize_factor = max(
            1.0 * min_width / orig_width, 1.0 * min_height / orig_height
        )
        new_width = int(resize_factor * orig_width)
        new_height = int(resize_factor * orig_height)
        return new_width, new_height
    return None


def generate_cover(
    file_name: Path, title_text: str, cover_options: CoverOptions, logger=None
):
    """
    Generate a plain image cover file

    :param file_name: Filename to be saved as
    :param title_text: Cover text
    :param cover_options: Cover options
    :param logger: Logger instance
    :return:
    """
    if not logger:
        logger = logging.getLogger(__file__)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)

    font_title = ImageFont.truetype(
        cover_options.title_font_path, cover_options.title_font_size
    )
    font_date = ImageFont.truetype(
        cover_options.datestamp_font_path, cover_options.datestamp_font_size
    )

    default_calibre_title_re = re.compile(r"(.+)\s\[(.+?)\]", re.IGNORECASE)

    title_texts = [t.strip() for t in title_text.split(":")]
    if len(title_texts) == 1:
        # not the expected newsrack-customised title
        # try to parse default calibre title format
        mobj = default_calibre_title_re.match(title_text)
        if mobj:
            title_texts = [str(t).strip() for t in mobj.groups()]

    with Image.new(
        "RGB",
        (cover_options.cover_width, cover_options.cover_height),
        color=cover_options.background_colour,
    ) as img:
        img_draw = ImageDraw.Draw(img)
        # rectangle outline
        if cover_options.border_width and cover_options.border_offset >= 0:
            img_draw.rectangle(
                (
                    cover_options.border_offset,
                    cover_options.border_offset,
                    cover_options.cover_width - cover_options.border_offset,
                    cover_options.cover_height - cover_options.border_offset,
                ),
                width=cover_options.border_width,
                outline=cover_options.text_colour,
            )

        total_height = 0
        text_w_h = []
        for i, text in enumerate(title_texts):
            if i == 0 and cover_options.title_font_size:
                max_chars_per_length = int(
                    1.5
                    * (
                        cover_options.cover_width
                        - 2 * (cover_options.border_offset + cover_options.border_width)
                    )
                    / cover_options.title_font_size
                )
                wrapper = textwrap.TextWrapper(width=max_chars_per_length)
                word_list = wrapper.wrap(text=text)

                for ii in word_list[:-1]:
                    _, __, text_w, text_h = img_draw.textbbox(
                        (0, 0), ii, font=font_title
                    )
                    text_w_h.append([ii, text_w, text_h, text_h, font_title])
                    total_height += text_h

                _, __, text_w, text_h = img_draw.textbbox(
                    (0, 0), word_list[-1], font=font_title
                )
                line_gap = int(cover_options.title_font_size / 4.0)
                text_w_h.append(
                    [word_list[-1], text_w, text_h, text_h + line_gap, font_title]
                )
                total_height += text_h + line_gap
            elif i > 0 and cover_options.datestamp_font_size:
                # also support multi-lines for the date string to support long text,
                # such as "Volume 12, Issue 4 January 2022"
                max_chars_per_length = int(
                    1.5
                    * (
                        cover_options.cover_width
                        - 2 * (cover_options.border_offset + cover_options.border_width)
                    )
                    / cover_options.datestamp_font_size
                )
                wrapper = textwrap.TextWrapper(width=max_chars_per_length)
                word_list = wrapper.wrap(text=text)

                for ii in word_list[:-1]:
                    _, __, text_w, text_h = img_draw.textbbox(
                        (0, 0), ii, font=font_date
                    )
                    text_w_h.append([ii, text_w, text_h, text_h, font_date])
                    total_height += text_h

                _, __, text_w, text_h = img_draw.textbbox(
                    (0, 0), word_list[-1], font=font_date
                )
                line_gap = int(cover_options.datestamp_font_size / 4.0)
                text_w_h.append(
                    [word_list[-1], text_w, text_h + line_gap, text_h, font_date]
                )
                total_height += text_h + line_gap

        if cover_options.logo_path_or_url:
            try:
                logo_buffer_gap_x = 0.05 * cover_options.cover_width
                logo_buffer_gap_y = 0.05 * cover_options.cover_height

                if os.path.exists(cover_options.logo_path_or_url):
                    image_pointer = cover_options.logo_path_or_url
                else:
                    res = requests.get(
                        cover_options.logo_path_or_url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=60,
                        stream=True,
                    )
                    res.raise_for_status()
                    image_pointer = res.raw

                with Image.open(image_pointer).convert("RGBA") as logo:
                    logo_max_width = int(
                        cover_options.cover_width
                        - 2 * (cover_options.border_offset + cover_options.border_width)
                        - 2 * logo_buffer_gap_x  # buffer space
                    )
                    logo_max_height = int(
                        (
                            cover_options.cover_height
                            - total_height
                            - 2
                            * (cover_options.border_offset + cover_options.border_width)
                            - 2 * logo_buffer_gap_y  # buffer space
                        )
                        / 2
                    )
                    if (logo.width / logo.height) >= 0.8:
                        # close to square-ish, so we reduce the max height a little
                        # so that there's a little more space above the text
                        logo_max_height = int(logo_max_height * 0.9)

                    logo_new_size = calc_resize(
                        (logo_max_width, logo_max_height), logo.size
                    )
                    if logo_new_size:
                        logger.debug(f"Resizing logo to {logo_new_size}")
                        logo = logo.resize(logo_new_size)

                    background = Image.new(
                        "RGBA", logo.size, cover_options.background_colour
                    )
                    logo_alpha_composite = Image.alpha_composite(background, logo)
                    logo_pos_x = int((cover_options.cover_width - logo.width) / 2)
                    logo_pos_y = int(
                        cover_options.border_offset
                        + cover_options.border_width
                        + logo_buffer_gap_y
                    )
                    img.paste(logo_alpha_composite, (logo_pos_x, logo_pos_y))

            except Exception:  # noqa, pylint: disable=broad-except
                # fail gracefully since logo is not absolutely necessary
                logger.exception(
                    "Error processing cover logo: %s", cover_options.logo_path_or_url
                )

        text_start_pos_y = int(
            (cover_options.cover_height - total_height) / 2
            + cover_options.border_offset
            + cover_options.border_width
        )
        if not cover_options.logo_path_or_url:
            # we can bump up the text title a little to make it look better
            text_start_pos_y -= int(cover_options.title_font_size / 2)

        cumu_offset = 0
        for text, text_w, text_h, h_offset, font in text_w_h:
            img_draw.text(
                (
                    int((cover_options.cover_width - text_w) / 2),
                    text_start_pos_y + cumu_offset,
                ),
                text,
                font=font,
                fill=cover_options.text_colour,
            )
            cumu_offset += h_offset
        img.save(file_name)
