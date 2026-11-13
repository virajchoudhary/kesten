import os


DEFAULT_PRODUCT_NAME = "Kerquant"
PRODUCT_NAME = (
    os.environ.get("NEXT_PUBLIC_PRODUCT_NAME", DEFAULT_PRODUCT_NAME).strip()
    or DEFAULT_PRODUCT_NAME
)


def page_title(section=""):
    return f"{section} - {PRODUCT_NAME}" if section else PRODUCT_NAME
