from rich.highlighter import RegexHighlighter


class ApduHighlighter(RegexHighlighter):

    base_style = "apdu."
    highlights = [
        # Class name (e.g., Apdu)
        r"(?P<class_name>\w+)\(",
        # CLA (2 hex digits)
        r"(?P<cla>[0-9A-F]{2})\s",
        # INS (2 hex digits)
        r"(?P<ins>[0-9A-F]{2})\s",
        # P1 (2 hex digits)
        r"(?P<p1>[0-9A-F]{2})\s",
        # P2 (2 hex digits)
        r"(?P<p2>[0-9A-F]{2})\s",
        # P3 (2 hex digits)
        r"(?P<p3>[0-9A-F]{2})\s",
        # Command Data (hex bytes separated by spaces)
        r"(?P<cmd_data>(?:[0-9A-F]{2}\s?)+)",
        # Response Data (hex bytes separated by spaces)
        r"(?P<rsp_data>(?:[0-9A-F]{2}\s?)+)",
        # SW (4 hex digits)
        r"(?P<sw>[0-9A-F]{4})\)",
    ]
