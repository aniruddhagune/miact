from backend.services.extractors.notebookcheck import parse_html


def load_notebookcheck_fixture() -> tuple[str, str]:
    fixture_path = "context/notebookcheck.txt"
    with open(fixture_path, "r", encoding="utf-8") as f:
        raw = f.read()

    url_marker = "URL:"
    html_marker = "HTML:"

    url_start = raw.find(url_marker)
    html_start = raw.find(html_marker)

    if url_start == -1 or html_start == -1:
        raise RuntimeError("Notebookcheck fixture is missing URL or HTML markers.")

    url_line = raw[url_start + len(url_marker):].splitlines()[0].strip()
    html = raw[html_start + len(html_marker):].strip()
    return url_line, html


def main():
    url, html = load_notebookcheck_fixture()
    data = parse_html(html, url)

    if not data:
        raise RuntimeError("Notebookcheck extractor returned no data.")

    print("Title:", data["title"])
    print("Published:", data["published_at"])
    print("Table count:", len(data.get("tables", [])))
    print("Opinion count:", len(data.get("opinions", [])))

    sample_specs = data.get("tables", [])[:8]
    print("\n--- SAMPLE SPECS ---")
    for row in sample_specs:
        print(f"[{row['aspect']}] {row['value']}")

    sample_opinions = data.get("opinions", [])[:6]
    print("\n--- SAMPLE OPINIONS ---")
    for row in sample_opinions:
        print(f"[{row['source']}] {row['text']}")


if __name__ == "__main__":
    main()
