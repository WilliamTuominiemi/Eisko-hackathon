from pdf2image import convert_from_path
import os
from typing import Optional, List
from PIL import Image


def convert_pdf_to_images(
    pdf_path: str,
    output_dir: str = 'pages',
    pages: Optional[List[int]] = [4],
    dpi: int = 300,
    poppler_path: Optional[str] = '/opt/homebrew/bin',
    return_images: bool = False,
) -> Optional[List[Image.Image]]:
    if not return_images:
        os.makedirs(output_dir, exist_ok=True)

    # Determine page range
    if pages is None:
        # Convert all pages
        first_page = None
        last_page = None
    elif len(pages) == 1:
        # Single page
        first_page = pages[0]
        last_page = pages[0]
    else:
        # Multiple specific pages - convert range and filter later
        first_page = min(pages)
        last_page = max(pages)

    images = convert_from_path(
        pdf_path,
        poppler_path=poppler_path,
        first_page=first_page,
        last_page=last_page,
        dpi=dpi,
    )

    # Filter to specific pages if needed
    if pages is not None and len(pages) > 1:
        filtered_images = []
        for i, img in enumerate(images, start=first_page or 1):
            if i in pages:
                filtered_images.append(img)
        images = filtered_images

    if return_images:
        return images

    # Save images to disk
    saved_paths = []
    page_num = pages[0] if pages and len(pages) == 1 else (first_page or 1)

    for i, image in enumerate(images):
        # Use actual page number in filename
        actual_page = pages[i] if pages and i < len(pages) else page_num + i
        output_path = os.path.join(output_dir, f'page_{actual_page}.jpg')
        image.save(output_path, 'JPEG')
        saved_paths.append(output_path)
        print(f'Saved {output_path}')

    return None
