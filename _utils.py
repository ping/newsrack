import textwrap

from PIL import Image, ImageDraw, ImageFont

# for cover generation
font_big = ImageFont.truetype("static/OpenSans-Bold.ttf", 82)
font_med = ImageFont.truetype("static/OpenSans-Semibold.ttf", 72)


def generate_cover(file_name, title_text, cover_width=889, cover_height=1186):
    """
    Generate a plain image cover file

    :param file_name: Filename to be saved as
    :param title_text: Cover text
    :param cover_width: Width
    :param cover_height: Height
    :return:
    """
    rectangle_offset = 25
    title_texts = [t.strip() for t in title_text.split(":")]

    img = Image.new("RGB", (cover_width, cover_height), color="white")
    img_draw = ImageDraw.Draw(img)
    # rectangle outline
    img_draw.rectangle(
        (
            rectangle_offset,
            rectangle_offset,
            cover_width - rectangle_offset,
            cover_height - rectangle_offset,
        ),
        width=2,
        outline="black",
    )

    total_height = 0
    line_gap = 25
    text_w_h = []
    for i, text in enumerate(title_texts):
        if i == 0:
            wrapper = textwrap.TextWrapper(width=15)
            word_list = wrapper.wrap(text=text)

            for ii in word_list[:-1]:
                text_w, text_h = img_draw.textsize(ii, font=font_big)
                text_w_h.append([ii, text_w, text_h, text_h, font_big])
                total_height += text_h + line_gap

            text_w, text_h = img_draw.textsize(word_list[-1], font=font_big)
            text_w_h.append([word_list[-1], text_w, text_h, text_h, font_big])
            total_height += text_h + line_gap
        else:
            text_w, text_h = img_draw.textsize(text, font=font_med)
            text_w_h.append([text, text_w, text_h, text_h, font_med])
            total_height += text_h + line_gap

    cumu_offset = 0
    for text, text_w, text_h, h_offset, font in text_w_h:
        img_draw.text(
            (
                int((cover_width - text_w) / 2),
                int((cover_height - total_height) / 2) + cumu_offset,
            ),
            text,
            font=font,
            fill="black",
        )
        cumu_offset += h_offset
    img.save(file_name)
