from pdf_to_jpeg import convert_pdf_to_images
from extract_components import do_extraction
from suoja import extract_suoja_values_from_image
from make_comparisons import compare_components
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
    cell_counter = 0
    pages_processed = 0
    pages_skipped = 0

    for page_file in page_files:
        page_name = os.path.basename(page_file)

        print(f'\nProcessing {page_name}...')

        try:
            cell_images = do_extraction(page_file)

            if not cell_images:
                print(f'  Skipping {page_name}: No components extracted')
                pages_skipped += 1
                continue

            num_cells = len(cell_images)
            print(f'  Extracted {num_cells} cells from {page_name}')
            total_cells += num_cells

            # Save cell images for comparison
            for i, cell_img in enumerate(cell_images):
                cell_img.save(os.path.join(out_dir, f'cell_{cell_counter}.png'))
                cell_counter += 1

            suoja_values = extract_suoja_values_from_image(
                page_file,
                use_ocr=True,
                save_crops=True,
                output_folder='suoja_extracts',
            )
            print(f'  Extracted {len(suoja_values)} suoja values: {suoja_values}')

            all_suoja_values.extend(suoja_values)
            pages_processed += 1

        except Exception as e:
            print(f'  Error processing {page_name}: {str(e)}')
            pages_skipped += 1
            continue

    print(f'\n{"=" * 60}')
    print('SUMMARY:')
    print(f'{"=" * 60}')
    print(f'Pages processed: {pages_processed}/{len(page_files)}')
    if pages_skipped > 0:
        print(f'Pages skipped: {pages_skipped}')
    print(f'Total cells extracted: {total_cells}')
    print(f'Total Suoja values: {len(all_suoja_values)}')
    print(f'\nAll Suoja values: {all_suoja_values}')

    # Compare components to find unique items
    if all_suoja_values and total_cells > 0:
        print(f'\n{"=" * 60}')
        print('COMPARING COMPONENTS...')
        print(f'{"=" * 60}')
        unique_components = compare_components(
            all_suoja_values,
            cells_dir=out_dir,
        )

        print(f'\nUnique components: {len(unique_components)}')
        print(f'\n{"Component":<30} {"Count":>10}')
        print(f'{"-" * 42}')
        for (filename, label), count in sorted(
            unique_components.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f'{label:<30} {count:>10}')

    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
