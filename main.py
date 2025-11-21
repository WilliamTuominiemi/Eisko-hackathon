from pdf_to_jpeg import convert_pdf_to_images
from extract_component_cells import extract_cells_from_image
import os
import glob


def main():
    print("Converting PDF to images...")
    convert_pdf_to_images("example.pdf")

    print("\nExtracting cells from each page...")
    pages_dir = "pages"
    out_dir = "extracted_cells"
    page_files = sorted(glob.glob(os.path.join(pages_dir, "page_*.jpg")))

    if not page_files:
        print(f"No page files found in {pages_dir}")
        return

    # Create single output directory for all cells from all pages
    os.makedirs(out_dir, exist_ok=True)

    total_cells = 0
    for page_file in page_files:
        page_name = os.path.basename(page_file)
        page_num = page_name.replace("page_", "").replace(".jpg", "")

        print(f"\nProcessing {page_name}...")
        num_cells = extract_cells_from_image(
            page_file, out_dir=out_dir, prefix=f"page_{page_num}_cell"
        )

        print(f"  Extracted {num_cells} cells from {page_name}")
        total_cells += num_cells

    print(f"\n{'=' * 60}")
    print(f"Total cells extracted from all pages: {total_cells}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
