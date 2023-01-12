import os


def format_title(feed_name, post_date):
    """
    Format title
    :return:
    """
    try:
        var_value = os.environ["newsrack_title_dt_format"]
        return f"{feed_name}: {post_date:{var_value}}"
    except:  # noqa
        return f"{feed_name}: {post_date:%-d %b, %Y}"
