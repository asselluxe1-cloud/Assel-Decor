import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace


BASE_DIR = Path(__file__).resolve().parent


# CONFIG
with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


pre_order_days = int(config.get("pre_order_days", 2))

merchant_id = str(config.get("merchantid", ""))
default_store_id = str(config.get("store_id", ""))

prices = config.get("prices", {})


# PRODUCTS
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
        "current_price"
    }

    missing = required - set(reader.fieldnames or [])

    if missing:
        raise ValueError(
            "products.csv ішінде бағандар жетіспейді: "
            + ", ".join(sorted(missing))
        )

    for row in reader:

        sku = row["sku"].strip()

        if not sku:
            continue

        size = row["size"].strip().lower().replace(" ", "")

        store_id = row["store_id"].strip() or default_store_id

        stock_count = int(float(row["stock_count"] or 0))

        current_price = row["current_price"].strip()

        if current_price:
            current_price = int(float(current_price))
        else:
            current_price = 0


        if sku not in products:

            products[sku] = {
                "model": row["model"].strip(),
                "brand": row["brand"].strip(),
                "size": size,
                "current_price": current_price,
                "availabilities": []
            }


        products[sku]["availabilities"].append({
            "store_id": store_id,
            "stock_count": stock_count
        })


# KASPI XML
register_namespace("", "kaspiShopping")

date_string = datetime.now(timezone.utc).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)


root = Element(
    "kaspi_catalog",
    {
        "date": date_string,
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation":
            "kaspiShopping http://kaspi.kz/kaspishopping.xsd"
    }
)


SubElement(root, "company").text = "Assel Decor"

SubElement(root, "merchantid").text = merchant_id


offers = SubElement(root, "offers")


for sku, product in products.items():

    size = product["size"]

    # Егер config.json ішінде осы өлшемге арнайы баға болса,
    # сол баға қолданылады.
    # Басқа өлшемдер products.csv-дегі қазіргі бағасын сақтайды.
    price = prices.get(size, product["current_price"])


    offer = SubElement(
        offers,
        "offer",
        {
            "sku": sku
        }
    )


    SubElement(
        offer,
        "model"
    ).text = product["model"]


    SubElement(
        offer,
        "brand"
    ).text = product["brand"]


    availabilities = SubElement(
        offer,
        "availabilities"
    )


    for availability in product["availabilities"]:

        stock = availability["stock_count"]

        store_id = availability["store_id"]


        SubElement(
            availabilities,
            "availability",
            {
                "available": "yes",
                "storeId": store_id,
                "preOrder": str(pre_order_days),
                "stockCount": str(stock)
            }
        )


    SubElement(
        offer,
        "price"
    ).text = str(price)


# SAVE
output = BASE_DIR / "kaspi.xml"

tree = ElementTree(root)

tree.write(
    output,
    encoding="utf-8",
    xml_declaration=True
)


print("Kaspi XML дайын.")
print(f"Тауар саны: {len(products)}")
print(f"PreOrder: {pre_order_days} күн")
print(f"Merchant ID: {merchant_id}")
print(f"Store ID: {default_store_id}")
print(f"XML: {output}")
