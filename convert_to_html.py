#!/usr/bin/env python3
"""convert_to_html.py

Reads a CSV or JSON file and writes a simple HTML file containing a table
with three columns. Usage examples are in README.md.
"""
import argparse
import csv
import html
import json
import sys
from pathlib import Path


def read_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            rows.append(r)
    return rows


def read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Accept list of lists or list of dicts
    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            # use dict values (order not guaranteed) -> require headers
            return data
        else:
            return data
    raise ValueError("Unsupported JSON structure: expected list of lists or list of objects")


def rows_from_json_data(data, headers):
    # If data is list of dicts, produce rows according to headers
    if not data:
        return []
    if isinstance(data[0], dict):
        if not headers:
            # pick first three keys
            keys = list(data[0].keys())[:3]
        else:
            keys = headers
        rows = [keys]
        for obj in data:
            rows.append([str(obj.get(k, "")) for k in keys])
        return rows
    else:
        # assume list of lists
        return data


def ensure_three_columns(rows, headers_provided=False):
    out = []
    for r in rows:
        # convert any non-list (e.g., dict) to list of values
        if isinstance(r, dict):
            r = list(r.values())
        # pad or truncate to 3 columns
        r = [str(x) for x in r]
        if len(r) < 3:
            r = r + [""] * (3 - len(r))
        else:
            r = r[:3]
        out.append(r)
    # If headers were not provided and first row has anything, keep as-is
    return out


SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


def looks_like_image(value):
    if not isinstance(value, str):
        return False
    candidate = value.strip().lower()
    if candidate.startswith("data:image/"):
        for fmt in ("png", "jpeg", "jpg"):
            if candidate.startswith(f"data:image/{fmt}"):
                return True
        return False
    candidate = candidate.split("?", 1)[0].split("#", 1)[0]
    return candidate.endswith(SUPPORTED_IMAGE_EXTENSIONS)


def image_paths_from_directory(directory):
    dir_path = Path(directory).expanduser()
    if not dir_path.exists():
        raise ValueError(f"Image directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Image directory is not a directory: {dir_path}")
    images = sorted(
        (p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )
    return [p.as_posix() for p in images]


def image_alt_text(src):
    stripped = src.strip()
    lower = stripped.lower()
    if lower.startswith("data:image/"):
        fmt = lower.split(";", 1)[0].split("/", 1)[-1]
        return f"{fmt.upper()} image"
    base = src.strip().rstrip("/").split("/")[-1]
    base = base.split("?", 1)[0].split("#", 1)[0]
    if not base:
        return "Image"
    return Path(base).stem or "Image"


def image_html(src, use_tailwind):
    escaped_src = html.escape(src.strip(), quote=True)
    alt = html.escape(image_alt_text(src), quote=True)
    if use_tailwind:
        return f'<img src="{escaped_src}" alt="{alt}" class="h-16 object-contain" />'
    return f'<img src="{escaped_src}" alt="{alt}" style="max-height: 120px; object-fit: contain;" />'


def generate_html(rows, headers=None, title="Table", use_tailwind=True, row_images=None):
    # rows: list of rows (including header if provided)
    image_iter = iter(row_images) if row_images else None

    def consume_image():
        if image_iter is None:
            return None
        return next(image_iter, None)

    html = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        f"<meta charset=\"utf-8\">",
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        f"<title>{title}</title>",
    ]

    if use_tailwind:
        # Use Tailwind CDN for quick styling
        html.append("<script src=\"https://cdn.tailwindcss.com\"></script>")
        html.append("</head>")
        html.append("<body class=\"bg-gray-50 text-gray-900 p-6\">")
        html.append(f"<div class=\"max-w-6xl mx-auto bg-white shadow rounded-lg overflow-hidden\">")
        html.append(f"<div class=\"p-6\"><h2 class=\"text-2xl font-semibold mb-4\">{title}</h2>")
        # Table container
        html.append("<div class=\"overflow-x-auto\">")
        html.append("<table class=\"min-w-full divide-y divide-gray-200 table-auto\">")
    else:
        # Minimal fallback styles
        css = (
            "table { border-collapse: collapse; width: 100%; }"
            "th, td { border: 1px solid #ddd; padding: 8px; }"
            "th { background: #f4f4f4; text-align: left; }"
        )
        html.append("<style>")
        html.append(css)
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append(f"<h2>{title}</h2>")
        html.append("<table>")

    def add_row_cells(cells, tag="td", header=False, image_src=None):
        parts = []
        processed_cells = list(cells)
        if not header and image_src is not None:
            if processed_cells:
                processed_cells[0] = image_src
            else:
                processed_cells = [image_src]
        for c in processed_cells:
            text = str(c)
            if not header and looks_like_image(text):
                cell_content = image_html(text, use_tailwind)
            else:
                cell_content = text
            if use_tailwind:
                if tag == "th":
                    parts.append(f"<th class=\"px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider\">{cell_content}</th>")
                else:
                    parts.append(f"<td class=\"px-6 py-4 whitespace-nowrap text-sm text-gray-700\">{cell_content}</td>")
            else:
                parts.append(f"<{tag}>{cell_content}</{tag}>")
        return "".join(parts)

    # If headers provided explicitly
    if headers:
        if use_tailwind:
            html.append("<thead class=\"bg-gray-50\">")
            html.append("<tr>")
            html.append(add_row_cells(headers, tag="th", header=True))
            html.append("</tr>")
            html.append("</thead>")
            html.append("<tbody class=\"bg-white divide-y divide-gray-200\">")
        else:
            html.append("<thead>")
            html.append("<tr>")
            html.append(add_row_cells(headers, tag="th", header=True))
            html.append("</tr>")
            html.append("</thead>")
            html.append("<tbody>")

        for r in rows:
            html.append("<tr>")
            html.append(add_row_cells(r, image_src=consume_image()))
            html.append("</tr>")
        html.append("</tbody>")
    else:
        # If first row looks like header (has strings), treat as header
        if rows and all(isinstance(c, str) for c in rows[0]):
            first = rows[0]
            rest = rows[1:]
            if use_tailwind:
                html.append("<thead class=\"bg-gray-50\">")
                html.append("<tr>")
                html.append(add_row_cells(first, tag="th", header=True))
                html.append("</tr>")
                html.append("</thead>")
                html.append("<tbody class=\"bg-white divide-y divide-gray-200\">")
            else:
                html.append("<thead>")
                html.append("<tr>")
                html.append(add_row_cells(first, tag="th", header=True))
                html.append("</tr>")
                html.append("</thead>")
                html.append("<tbody>")

            for r in rest:
                html.append("<tr>")
                html.append(add_row_cells(r, image_src=consume_image()))
                html.append("</tr>")
            html.append("</tbody>")
        else:
            if use_tailwind:
                html.append("<tbody class=\"bg-white divide-y divide-gray-200\">")
            else:
                html.append("<tbody>")
            for r in rows:
                html.append("<tr>")
                html.append(add_row_cells(r, image_src=consume_image()))
                html.append("</tr>")
            html.append("</tbody>")

    # Close tags
    if use_tailwind:
        html.append("</table>")
        html.append("</div>")
        html.append("</div>")
        html.append("</div>")
        html.append("</body>")
        html.append("</html>")
    else:
        html.extend(["</table>", "</body>", "</html>"])

    return "\n".join(html)


def main():
    p = argparse.ArgumentParser(description="Convert CSV or JSON to HTML table with three columns.")
    p.add_argument("-i", "--input", required=True, help="Input file path (CSV or JSON)")
    p.add_argument("-o", "--output", default="output.html", help="Output HTML file path")
    p.add_argument("-t", "--title", default="Table", help="HTML page title")
    p.add_argument("--tailwind", action="store_true", help="Include Tailwind CSS via CDN for styling")
    p.add_argument("--headers", help="Comma-separated headers for the table (3 values)")
    p.add_argument("--image-dir", help="Directory containing photos to insert into the first column")
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        sys.exit(2)

    fmt = inp.suffix.lower().lstrip('.')
    headers = None
    if args.headers:
        headers = [h.strip() for h in args.headers.split(",")]
        if len(headers) != 3:
            print("--headers must contain exactly 3 comma-separated values", file=sys.stderr)
            sys.exit(2)

    use_tailwind = args.tailwind
    image_sources = None
    if args.image_dir:
        try:
            image_sources = image_paths_from_directory(args.image_dir)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(2)
        if not image_sources:
            print(f"No supported images found in {args.image_dir}", file=sys.stderr)

    if fmt in ("csv",):
        rows = read_csv(inp)
        rows = ensure_three_columns(rows)
        html = generate_html(rows, headers=headers, title=args.title, use_tailwind=use_tailwind, row_images=image_sources)
    elif fmt in ("json",):
        data = read_json(inp)
        # If list-of-dicts, convert using headers
        if isinstance(data, list) and data and isinstance(data[0], dict):
            rows = rows_from_json_data(data, headers)
            rows = ensure_three_columns(rows, headers_provided=bool(headers))
            if rows:
                derived_headers = headers if headers is not None else rows[0]
                body_rows = rows[1:]
            else:
                derived_headers = headers
                body_rows = rows
            html = generate_html(body_rows, headers=derived_headers, title=args.title, use_tailwind=use_tailwind, row_images=image_sources)
        else:
            rows = ensure_three_columns(data)
            html = generate_html(rows, headers=headers, title=args.title, use_tailwind=use_tailwind, row_images=image_sources)
    else:
        print(f"Unsupported input format: .{fmt}. Use .csv or .json", file=sys.stderr)
        sys.exit(2)

    outp = Path(args.output)
    outp.write_text(html, encoding="utf-8")
    print(f"Wrote HTML to {outp}")


if __name__ == "__main__":
    main()
