# ============================================================
# KASPI XML
# ============================================================

KASPI_NS = "kaspiShopping"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

register_namespace("", KASPI_NS)
register_namespace("xsi", XSI_NS)

date_string = datetime.now(
    timezone.utc
).strftime("%Y-%m-%dT%H:%M:%SZ")

root = Element(
    f"{{{KASPI_NS}}}kaspi_catalog",
    {
        "date": date_string,
        f"{{{XSI_NS}}}schemaLocation":
            "kaspiShopping http://kaspi.kz/kaspishopping.xsd"
    }
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

for sku, product in products.items():

    offer = SubElement(
        offers,
        f"{{{KASPI_NS}}}offer",
        {"sku": sku}
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

    for availability in product["availabilities"]:

        SubElement(
            availabilities,
            f"{{{KASPI_NS}}}availability",
            {
                "available": "yes",
                "storeId": availability["store_id"],
                "preOrder": "2",
                "stockCount":
                    str(availability["stock_count"])
            }
        )

    SubElement(
        offer,
        f"{{{KASPI_NS}}}price"
    ).text = str(
        calculate_price(product)
    )


output = BASE_DIR / "kaspi.xml"

ElementTree(root).write(
    output,
    encoding="utf-8",
    xml_declaration=True
)
