from pdf_to_jpeg import convert_pdf_to_images
from extract_components import do_extraction
import os
import glob


def main():
    print('Converting PDF to images...')
    convert_pdf_to_images('example.pdf')

    print('\nExtracting cells and suoja values from each page...')
    out_dir = 'extracted_cells'
    page_files = sorted(glob.glob(os.path.join('pages', 'page_*.jpg')))

    if not page_files:
        print('No page files found in pages dir')
        return

    os.makedirs(out_dir, exist_ok=True)

    total_cells = 0
    all_suoja_values = []

    for page_file in page_files:
        page_name = os.path.basename(page_file)

        print(f'\nProcessing {page_name}...')

        (cell_images, component_with_suoja) = do_extraction(page_file)
        num_cells = len(cell_images)
        print(f'  Extracted {num_cells} cells from {page_name}')
        total_cells += num_cells

        # suoja_values = extract_suoja_values_from_image(
        #     page_file,
        #     use_ocr=True,
        #     save_crops=True,
        #     output_folder='suoja_extracts',
        # )
        # print(f'  Extracted {len(suoja_values)} suoja values: {suoja_values}')

        # all_suoja_values.extend(suoja_values)

    print(f'\n{"=" * 60}')
    print('SUMMARY:')
    print(f'{"=" * 60}')
    print(f'Total cells extracted: {total_cells}')
    print(f'Total Suoja values: {len(all_suoja_values)}')
    print(f'\nAll Suoja values: {all_suoja_values}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
