import streamlit as st
import tempfile
import os
import shutil
import glob
from pdf_to_jpeg import convert_pdf_to_images
from suoja import extract_suoja_values_from_image
from make_comparisons import compare_components
from extract_components import do_extraction

st.set_page_config(page_title='Component counter', page_icon='📋')

st.title('Switchboard component counter')
st.write('Upload a PDF file to count unique components')

# File uploader
uploaded_file = st.file_uploader('Choose a PDF file', type=['pdf'])

if uploaded_file is not None:
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Process button
    if st.button('Analyze switchboard', type='primary'):
        try:
            # Create temporary directories for processing
            cells_dir = tempfile.mkdtemp()

            with st.spinner('Converting PDF to images...'):
                # Convert PDF to images (all pages, outputs to 'pages' directory)
                convert_pdf_to_images(tmp_path)

            with st.spinner('Extracting cells and suoja values from all pages...'):
                # Get all page files
                page_files = sorted(glob.glob(os.path.join('pages', 'page_*.jpg')))

                if not page_files:
                    st.error('No pages were extracted from the PDF')
                else:
                    # Process all pages
                    all_cell_images = []
                    all_suoja_values = []
                    total_cells = 0
                    cell_counter = 0
                    pages_processed = 0
                    pages_skipped = 0

                    for page_file in page_files:
                        page_name = os.path.basename(page_file)

                        try:
                            # Extract table cells (with optimizations: in-memory processing)
                            cell_images = do_extraction(page_file)

                            if not cell_images:
                                print(f'Skipping {page_name}: No components extracted')
                                pages_skipped += 1
                                continue

                            num_cells = len(cell_images)
                            total_cells += num_cells

                            # Save cells temporarily for comparison
                            for i, cell_img in enumerate(cell_images):
                                cell_img.save(
                                    os.path.join(cells_dir, f'cell_{cell_counter}.png')
                                )
                                cell_counter += 1

                            all_cell_images.extend(cell_images)

                            # Extract Suoja values (with optimizations: parallel OCR)
                            suoja_values = extract_suoja_values_from_image(
                                page_file,
                                use_ocr=True,
                                save_crops=False,
                                parallel=True,
                            )
                            all_suoja_values.extend(suoja_values)
                            pages_processed += 1

                        except Exception as e:
                            print(f'Error processing {page_name}: {str(e)}')
                            pages_skipped += 1
                            continue

                    num_cells = total_cells
                    suoja_values = all_suoja_values

                    # Display results
                    if pages_skipped > 0:
                        st.warning(
                            f'Extraction completed: {pages_processed} page(s) processed, {pages_skipped} page(s) skipped'
                        )
                    else:
                        st.success(
                            f'Extraction completed from {pages_processed} page(s)'
                        )

                    st.subheader('Results')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            'Pages processed', f'{pages_processed}/{len(page_files)}'
                        )
                    with col2:
                        st.metric('Cells extracted', num_cells)
                    with col3:
                        st.metric('Suoja values extracted', len(suoja_values))

                    # Compare components to find unique items
                    if len(suoja_values) != num_cells:
                        st.warning(
                            f'Warning: Number of suoja values ({len(suoja_values)}) does not match number of cells ({num_cells})'
                        )

                    if suoja_values and num_cells > 0:
                        with st.spinner('Comparing components...'):
                            unique_components = compare_components(
                                suoja_values,
                                cells_dir=cells_dir,
                            )

                        st.subheader('Unique components')
                        st.metric('Total unique components', len(unique_components))

                        # Display unique components with images
                        if unique_components:
                            for (filename, label), count in sorted(
                                unique_components.items(),
                                key=lambda x: x[1],
                                reverse=True,
                            ):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    # Display the component image
                                    image_path = os.path.join(cells_dir, filename)
                                    if os.path.exists(image_path):
                                        st.image(image_path, use_container_width=True)
                                with col2:
                                    st.write(f'**Label:** {label}')
                                    st.write(f'**Count:** {count}')
                                st.divider()
                    else:
                        st.info('No components to compare')

                    # Clean up temporary directories
                    shutil.rmtree(cells_dir)
                    # Clean up pages directory
                    if os.path.exists('pages'):
                        shutil.rmtree('pages')

        except Exception as e:
            st.error(f'Error processing PDF: {str(e)}')
            import traceback

            st.error(traceback.format_exc())

        finally:
            # Clean up the temporary PDF file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        # Clean up if button not pressed
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

else:
    st.info('Upload a PDF file to get started')

    st.markdown("""
    ### How to use
    1. Upload a PDF file
    2. Click "Analyze switchboard"
    3. View unique components and their counts
    """)
