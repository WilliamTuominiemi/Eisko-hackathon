import streamlit as st
import tempfile
import os
import shutil
from pdf_to_jpeg import convert_pdf_to_images
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
            with st.spinner('Converting PDF page 2 to image...'):
                # Convert PDF to images (page 2 only, outputs to 'pages' directory)
                convert_pdf_to_images(tmp_path)

            with st.spinner('Extracting cells and suoja values from page 2...'):
                # Get the page file
                page_file = os.path.join('pages', 'page_2.jpg')

                if not os.path.exists(page_file):
                    st.error('Page 2 was not extracted from the PDF')
                else:
                    # Extract table cells (with optimizations: in-memory processing)
                    (cell_images, component_with_suoja) = do_extraction(page_file)

                    num_cells = len(cell_images)

                    # Display results
                    st.success('Extraction completed')

                    st.subheader('Results')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric('Cells extracted', num_cells)
                    with col2:
                        st.metric('Components with suoja', len(component_with_suoja))

                    print(component_with_suoja)
                    print(len(component_with_suoja))

                    if component_with_suoja and num_cells > 0:
                        with st.spinner('Comparing components...'):
                            unique_components = compare_components(component_with_suoja)

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
                                    # filename is already the full path (e.g., 'components/component_01.jpg')
                                    if os.path.exists(filename):
                                        st.image(filename, use_container_width=True)
                                with col2:
                                    st.write(f'**Label:** {label}')
                                    st.write(f'**Count:** {count}')
                                st.divider()
                    else:
                        st.info('No components to compare')

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
