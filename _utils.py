import textwrap

from PIL import Image, ImageDraw, ImageFont  # type: ignore

from _recipe_utils import CoverOptions


def generate_cover(
    file_name: str,
    title_text: str,
    cover_options: CoverOptions,
):
    """
    Generate a plain image cover file

    :param file_name: Filename to be saved as
    :param title_text: Cover text
    :param cover_options: Cover options
    :return:
    """
    font_title = ImageFont.truetype(
        cover_options.title_font_path, cover_options.title_font_size
    )
    font_date = ImageFont.truetype(
        cover_options.datestamp_font_path, cover_options.datestamp_font_size
    )

    rectangle_offset = 25
    title_texts = [t.strip() for t in title_text.split(":")]

    img = Image.new(
        "RGB",
        (cover_options.cover_width, cover_options.cover_height),
        color=cover_options.background_colour,
    )
    img_draw = ImageDraw.Draw(img)
    # rectangle outline
    img_draw.rectangle(
        (
            rectangle_offset,
            rectangle_offset,
            cover_options.cover_width - rectangle_offset,
            cover_options.cover_height - rectangle_offset,
        ),
        width=2,
        outline=cover_options.text_colour,
    )

    total_height = 0
    line_gap = 25
    text_w_h = []
    for i, text in enumerate(title_texts):
        if i == 0:
            wrapper = textwrap.TextWrapper(width=15)
            word_list = wrapper.wrap(text=text)

            for ii in word_list[:-1]:
                _, __, text_w, text_h = img_draw.textbbox((0, 0), ii, font=font_title)
                text_w_h.append([ii, text_w, text_h, text_h, font_title])
                total_height += text_h + line_gap

            _, __, text_w, text_h = img_draw.textbbox(
                (0, 0), word_list[-1], font=font_title
            )
            text_w_h.append([word_list[-1], text_w, text_h, text_h, font_title])
            total_height += text_h + line_gap
        else:
            _, __, text_w, text_h = img_draw.textbbox((0, 0), text, font=font_title)
            text_w_h.append([text, text_w, text_h, text_h, font_date])
            total_height += text_h + line_gap

    cumu_offset = 0
    for text, text_w, text_h, h_offset, font in text_w_h:
        img_draw.text(
            (
                int((cover_options.cover_width - text_w) / 2),
                int((cover_options.cover_height - total_height) / 2) + cumu_offset,
            ),
            text,
            font=font,
            fill=cover_options.text_colour,
        )
        cumu_offset += h_offset
    img.save(file_name)
