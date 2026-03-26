def deduplicate_attributes(attributes):
    unique = []
    seen = set()

    for attr in attributes:
        key = (
            attr["aspect"],
            str(attr["value"]),
            str(attr.get("unit"))
        )

        if key not in seen:
            seen.add(key)
            unique.append(attr)

    return unique