import streamlit as st
import tempfile
import os
import shutil
from pdf_to_jpeg import convert_pdf_to_images
from make_comparisons import compare_components
from extract_components import do_extraction

st.set_page_config(page_title='Component counter', page_icon='📋')

# Custom CSS for wider container and reduced padding
st.markdown(
    """
<style>
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    div[data-testid="column"] {
        padding: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title('Switchboard component counter')
st.write('Upload a PDF file to count unique components')

# File uploader
uploaded_file = st.file_uploader('Choose a PDF file', type=['pdf'])

# Page selection
page_number = st.number_input(
    'Select page to analyze',
    min_value=1,
    max_value=100,
    value=12,
    step=1,
)

if uploaded_file is not None:
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Process button
    if st.button('Analyze switchboard', type='primary'):
        try:
            with st.spinner(f'Converting PDF page {page_number} to image...'):
                # Convert PDF to images (selected page only, outputs to 'pages' directory)
                convert_pdf_to_images(tmp_path, pages=[page_number])

            with st.spinner(f'Extracting components from page {page_number}...'):
                # Get the page file
                page_file = os.path.join('pages', f'page_{page_number}.jpg')

                if not os.path.exists(page_file):
                    st.error(f'Page {page_number} was not extracted from the PDF')
                else:
                    # Extract table cells (with optimizations: in-memory processing)
                    (cell_images, component_with_suoja) = do_extraction(page_file)

                    num_cells = len(cell_images)

                    # Display results
                    st.success('Extraction completed')

                    print(component_with_suoja)
                    print(len(component_with_suoja))

                    if component_with_suoja and num_cells > 0:
                        with st.spinner('Comparing components...'):
                            unique_components = compare_components(component_with_suoja)

                        st.subheader('Results')
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric('Total components', num_cells)
                        with col2:
                            st.metric('Total unique components', len(unique_components))

                        # Display unique components with images in table format
                        if unique_components:
                            # Table header
                            header_col1, header_col2, header_col3 = st.columns(
                                [3, 1, 1]
                            )
                            with header_col1:
                                st.markdown('**Component**')
                            with header_col2:
                                st.markdown('**Suoja**')
                            with header_col3:
                                st.markdown('**Count**')
                            st.markdown('---')

                            # Table rows
                            for (filename, label), count in sorted(
                                unique_components.items(),
                                key=lambda x: x[1],
                                reverse=True,
                            ):
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    # Display the component image
                                    # filename is already the full path (e.g., 'components/component_01.jpg')
                                    if os.path.exists(filename):
                                        st.image(filename, use_container_width=True)
                                with col2:
                                    st.markdown(
                                        f'<p style="font-size: 1.5rem; padding-left: .25rem;">{label}</p>',
                                        unsafe_allow_html=True,
                                    )
                                with col3:
                                    st.markdown(
                                        f'<p style="font-size: 1.5rem; padding-left: .25rem;">{count}</p>',
                                        unsafe_allow_html=True,
                                    )
                                st.markdown('---')
                    else:
                        st.info('No components to compare')

        except Exception as e:
            st.error(f'Error processing PDF: {str(e)}')
            import traceback

            st.error(traceback.format_exc())

        finally:
            # Clean up all temporary directories
            for temp_dir in ['pages', 'components', 'extracted_cells']:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

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
