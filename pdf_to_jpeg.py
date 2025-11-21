from pdf2image import convert_from_path

# Convert a specific page to image
images = convert_from_path(
    'example.pdf',
    first_page=4,  # page number (1-indexed)
    last_page=4,
    dpi=300  # higher DPI = better quality
)

# Save as JPEG
images[0].save('output_page.jpg', 'JPEG')