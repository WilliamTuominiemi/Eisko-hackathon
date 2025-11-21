from pdf2image import convert_from_path
import os
from typing import Optional


def convert_pdf_to_images(
    pdf_path: str,
    poppler_path: Optional[str] = "/opt/homebrew/bin",
) -> None:
    output_dir = "pages"
    os.makedirs(output_dir, exist_ok=True)

    images = convert_from_path(
        pdf_path,
        poppler_path=poppler_path,
        first_page=2,  # Skip the first page
        dpi=300,
    )

    for i, image in enumerate(images, start=2):
        output_path = os.path.join(output_dir, f"page_{i}.jpg")
        image.save(output_path, "JPEG")
        print(f"Saved {output_path}")
