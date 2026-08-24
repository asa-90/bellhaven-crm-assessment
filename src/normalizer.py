import re
import unicodedata


def normalize_text(value):
    """
    Normalize general text for comparison.
    """

    if value is None:
        return ""

    value = str(value)

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def normalize_name(value):
    """
    Normalize facility names.
    """

    return normalize_text(value)


def normalize_city(value):
    """
    Normalize city names.
    """

    return normalize_text(value)


def normalize_state(value):
    """
    Normalize state names.
    """

    return normalize_text(value)


def normalize_zip(value):
    """
    Normalize ZIP codes.
    """

    if value is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(value),
    )


def normalize_phone(value):
    """
    Normalize phone numbers.
    """

    if value is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(value),
    )


def normalize_address(value):
    """
    Normalize street addresses.
    """

    value = normalize_text(value)

    replacements = {
        " street ": " st ",
        " avenue ": " ave ",
        " road ": " rd ",
        " boulevard ": " blvd ",
        " drive ": " dr ",
        " lane ": " ln ",
        " court ": " ct ",
        " highway ": " hwy ",
    }

    value = f" {value} "

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value.strip()