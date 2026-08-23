import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import (
    Element,
    SubElement,
    ElementTree,
    register_namespace,
)

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

PRE_ORDER_DAYS = 2
MERCHANT_ID = str(config.get("merchantid", ""))
DEFAULT_STORE_ID = str(config.get("store_id", ""))


# ============================================================
# ASSEL DECOR — БАҒАЛАР
# ============================================================

NORMAL_PRICES = {
    "160x80": 49990,
    "100x70": 29990,
    "50x70": 14990,
}

LIGHT_CLOCK_PRICES = {
    "160x80": 65000,
    "100x70": 45000,
    "50x70": 20000,
}


# products.csv ішінде қазіргі бренд assel-luxe1
ALLOWED_BRANDS = {
    "assel-luxe1",
    "assel-decor",
    "assel decor",
    "assel luxe",
}


# ============================================================
# ӨЛШЕМДІ АНЫҚТАУ
# ============================================================

def normalize_size(size):

    value = (
        str(size or "")
        .lower()
        .replace(" ", "")
        .replace("см", "")
    )

    return {
        "80x160": "160x80",
        "160x80": "160x80",

        "70x100": "100x70",
        "100x70": "100x70",

        "70x50": "50x70",
        "50x70": "50x70",
    }.get(value, value)


# ============================================================
# ПОДСВЕТКА + САҒАТ
# ============================================================

def has_light_and_clock(model):

    model = str(model or "").lower()

    light_words = [
        "подсвет",
        "подсветкой",
        "подсветка",
        "свет",
        "жарық",
        "жарығымен",
        "жарығ",
    ]

    clock_words = [
        "час",
        "часы",
        "часами",
        "сағат",
        "сағатпен",
        "сағаты",
    ]

    has_light = any(
        word in model
        for word in light_words
    )

    has_clock = any(
        word in model
        for word in clock_words
    )

    return has_light and has_clock


# ============================================================
# БАҒАНЫ ЕСЕПТЕУ
# ============================================================

def calculate_price(product):

    size = normalize_size(
        product["size"]
    )

    # Подсветка + сағат
    if has_light_and_clock(
        product["model"]
    ):

        if size in LIGHT_CLOCK_PRICES:
            return LIGHT_CLOCK_PRICES[size]

    # Кәдімгі
    if size in NORMAL_PRICES:
        return NORMAL_PRICES[size]

    # Басқа өлшемдерге тимейміз
    return product["current_price"]


# ============================================================
# PRODUCTS.CSV ОҚУ
# ============================================================

products = {}

with open(
    BASE_DIR / "products.csv",
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    required = {
        "sku",
        "model",
        "brand",
        "size",
        "store_id",
        "stock_count",
        "current_price",
    }

    missing = (
        required
        - set(reader.fieldnames or [])
    )

    if missing:
        raise ValueError(
            "products.csv ішінде бағандар жетіспейді: "
            + ", ".join(sorted(missing))
        )

    for row in reader:

        brand = row["brand"].strip().lower()

        if brand not in ALLOWED_BRANDS:
            continue

        sku = row["sku"].strip()

        if not sku:
            continue

        try:
            stock_count = int(
                float(
                    row["stock_count"] or 0
                )
            )
        except (
            ValueError,
            TypeError
        ):
            stock_count = 0

        try:
            current_price = int(
                float(
                    row["current_price"] or 0
                )
            )
        except (
            ValueError,
            TypeError
        ):
            current_price = 0

        products[sku] = {
            "model": row["model"].strip(),
            "brand": row["brand"].strip(),
            "size": row["size"].strip(),
            "current_price": current_price,

            "availabilities": [
                {
                    "store_id":
                        row["store_id"].strip()
                        or DEFAULT_STORE_ID,

                    "stock_count":
                        stock_count,
                }
            ],
        }


if not products:

    raise RuntimeError(
        "products.csv ішінен тауар табылмады."
    )


# ============================================================
# ASSEL DECOR — KASPI DESCRIPTION
# ============================================================

description = """✨ ASSEL DECOR — интерьеріңізге ерекше сән мен жарқырау сыйлайтын сапалы картиналар ✨

💎 ҚАЗАҚША: Кристалл тастардың жарқырауы, эпоксидті смоланың жылтыр эффектісі және сапалы UV PRINT картинаның әрбір бөлшегін ерекше көрсетеді. 5 қабатты технология: кристалл тастар + эпоксидті смола + UV PRINT + MDF негізі + алюминий рама. 🇰🇿 Қазақстанда жасалады, 90% қол еңбегі. Үйге, кеңсеге немесе сыйлыққа тамаша таңдау.

💎 РУССКИЙ: Блеск кристаллов, глянцевый эффект эпоксидной смолы и качественная UV PRINT подчёркивают каждую деталь картины. 5-слойная технология: кристаллы + эпоксидная смола + UV PRINT + основа MDF + алюминиевая рама. 🇰🇿 Изготовлено в Казахстане, 90% ручной работы. Отличный выбор для дома, офиса или в подарок.

💎 ENGLISH: The shine of crystal stones, glossy epoxy resin and high-quality UV PRINT highlight every detail of the painting. 5-layer technology: crystal stones + epoxy resin + UV PRINT + MDF base + aluminum frame. 🇰🇿 Made in Kazakhstan, 90% handmade. A perfect choice for home, office or as a gift.

✨ ASSEL DECOR — сапа, жарқырау және стиль бір картинада!"""


# ============================================================
# KASPI XML
# ============================================================

KASPI_NS = "kaspiShopping"
XSI_NS = (
    "http://www.w3.org/2001/XMLSchema-instance"
)

register_namespace(
    "",
    KASPI_NS
)

register_namespace(
    "xsi",
    XSI_NS
)

date_string = datetime.now(
    timezone.utc
).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)

root = Element(
    f"{{{KASPI_NS}}}kaspi_catalog",
    {
        "date": date_string,

        f"{{{XSI_NS}}}schemaLocation":
            "kaspiShopping "
            "http://kaspi.kz/kaspishopping.xsd",
    },
)

SubElement(
    root,
    f"{{{KASPI_NS}}}company"
).text = "Assel Decor"

SubElement(
    root,
    f"{{{KASPI_NS}}}merchantid"
).text = MERCHANT_ID

offers = SubElement(
    root,
    f"{{{KASPI_NS}}}offers"
)


# ============================================================
# ТАУАРЛАРДЫ XML-ГЕ ЖАЗУ
# ============================================================

for sku, product in products.items():

    offer = SubElement(
        offers,
        f"{{{KASPI_NS}}}offer",
        {
            "sku": sku
        }
    )

    SubElement(
        offer,
        f"{{{KASPI_NS}}}model"
    ).text = product["model"]

    SubElement(
        offer,
        f"{{{KASPI_NS}}}brand"
    ).text = product["brand"]

    SubElement(
        offer,
        f"{{{KASPI_NS}}}description"
    ).text = description

    availabilities = SubElement(
        offer,
        f"{{{KASPI_NS}}}availabilities"
    )

    for availability in product[
        "availabilities"
    ]:

        SubElement(
            availabilities,
            f"{{{KASPI_NS}}}availability",
            {
                "available": "yes",

                "storeId":
                    availability["store_id"],

                # PREORDER = 2 КҮН
                "preOrder":
                    str(PRE_ORDER_DAYS),

                "stockCount":
                    str(
                        availability[
                            "stock_count"
                        ]
                    ),
            }
        )

    price = calculate_price(
        product
    )

    SubElement(
        offer,
        f"{{{KASPI_NS}}}price"
    ).text = str(price)


# ============================================================
# KASPI.XML САҚТАУ
# ============================================================

output = BASE_DIR / "kaspi.xml"

ElementTree(root).write(
    output,
    encoding="utf-8",
    xml_declaration=True,
)


# ============================================================
# LOG
# ============================================================

print("=" * 60)

print(
    "ASSEL DECOR — KASPI XML"
)

print("=" * 60)

print(
    f"Тауар саны: {len(products)}"
)

print(
    f"PreOrder: {PRE_ORDER_DAYS} күн"
)

print()

print(
    "160x80 кәдімгі          = 49 990 ₸"
)

print(
    "160x80 подсветка+сағат  = 65 000 ₸"
)

print(
    "100x70 кәдімгі          = 29 990 ₸"
)

print(
    "100x70 подсветка+сағат  = 45 000 ₸"
)

print(
    "50x70 кәдімгі           = 14 990 ₸"
)

print(
    "50x70 подсветка+сағат   = 20 000 ₸"
)

print()

print(
    f"XML дайын: {output}"
)

print("=" * 60)

