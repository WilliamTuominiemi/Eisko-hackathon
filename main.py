from pdf_to_jpeg import convert_pdf_to_images
from extract_components import do_extraction
from make_comparisons import compare_components
import os
import glob


def main():
    print('Converting PDF to images...')
    convert_pdf_to_images('example.pdf')

    print('\nExtracting cells and suoja values from each page...')
    page_files = sorted(glob.glob(os.path.join('pages', 'page_*.jpg')))

    if not page_files:
        print('No page files found in pages dir')
        return

    total_cells = 0
    all_component_with_suoja = {}

    for page_file in page_files:
        page_name = os.path.basename(page_file)

        print(f'\nProcessing {page_name}...')

        (cell_images, component_with_suoja) = do_extraction(page_file)
        num_cells = len(cell_images)
        print(f'  Extracted {num_cells} cells from {page_name}')
        print(f'  Found {len(component_with_suoja)} components with suoja values')

        total_cells += num_cells
        all_component_with_suoja.update(component_with_suoja)

    print(f'\n{"=" * 60}')
    print('SUMMARY:')
    print(f'{"=" * 60}')
    print(f'Total cells extracted: {total_cells}')
    print(f'Total components with suoja: {len(all_component_with_suoja)}')

    if all_component_with_suoja:
        print('\nComparing components to find unique ones...')
        unique_components = compare_components(all_component_with_suoja)

        print(f'\n{"=" * 60}')
        print('UNIQUE COMPONENTS:')
        print(f'{"=" * 60}')
        print(f'Total unique components: {len(unique_components)}')

        for (filename, label), count in sorted(
            unique_components.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f'\nComponent: {os.path.basename(filename)}')
            print(f'  Suoja value: {label}')
            print(f'  Count: {count}')

    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
