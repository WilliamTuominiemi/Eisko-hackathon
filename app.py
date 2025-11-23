import streamlit as st
import tempfile
import os
import shutil
from pdf2image import pdfinfo_from_path
from pdf_to_jpeg import convert_pdf_to_images
from make_comparisons import compare_components
from extract_components import do_extraction

st.set_page_config(page_title='Invoice Simplifier', page_icon='📋', layout='centered')
st.markdown(
    """
<style>
    .block-container {
        max-width: 900px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    div[data-testid="column"] {
        padding: 0.5rem;
    }
    h1 {
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .stButton button {
        font-weight: 500;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title('Invoice simplifier')
st.markdown('Analyzes invoices to identify and count unique electrical components.')
st.divider()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 2
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = None
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

uploaded_file = st.file_uploader(
    'Upload PDF Document',
    type=['pdf'],
)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Get total page count if file is new or changed
    if st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.last_uploaded_file = uploaded_file.name
        st.session_state.current_page = 2  # Reset to page 2 for new file
        try:
            pdf_info = pdfinfo_from_path(tmp_path, poppler_path='/opt/homebrew/bin')
            st.session_state.total_pages = pdf_info.get('Pages', 100)
        except Exception:
            st.session_state.total_pages = 100  # Default fallback

    total_pages = st.session_state.total_pages or 100

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button(
            'Previous Page',
            disabled=st.session_state.current_page <= 2,
            use_container_width=True,
        ):
            st.session_state.current_page -= 1
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='display: flex; align-items: center; justify-content: center; height: 38px;'><h3 style='margin: 0;'>Page {st.session_state.current_page} of {total_pages}</h3></div>",
            unsafe_allow_html=True,
        )
    with col3:
        if st.button(
            'Next page',
            disabled=st.session_state.current_page >= total_pages,
            use_container_width=True,
        ):
            st.session_state.current_page += 1
            st.rerun()

    st.divider()

    page_number = st.session_state.current_page

    results_placeholder = st.empty()

    # Automatically analyze the current page
    with results_placeholder.container():
        with st.spinner(f'Processing page {page_number}...'):
            try:
                # Convert PDF to images (selected page only, outputs to 'pages' directory)
                convert_pdf_to_images(tmp_path, pages=[page_number])

                # Get the page file
                page_file = os.path.join('pages', f'page_{page_number}.jpg')

                if not os.path.exists(page_file):
                    st.error(f'Page {page_number} was not extracted from the PDF')
                else:
                    (cell_images, component_with_suoja) = do_extraction(page_file)

                    num_cells = len(cell_images)

                    if component_with_suoja and num_cells > 0:
                        unique_components = compare_components(component_with_suoja)

                        st.subheader('Summary')
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric('Total components', num_cells)
                        with col2:
                            st.metric('Total unique components', len(unique_components))

                        # Display unique components with images in table format
                        if unique_components:
                            st.markdown('### Results')

                            # Table header
                            header_col1, header_col2, header_col3 = st.columns(
                                [3, 1, 1]
                            )
                            with header_col1:
                                st.markdown('**Component**')
                            with header_col2:
                                st.markdown('**Protection ID**')
                            with header_col3:
                                st.markdown('**Quantity**')
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
                                        f'<p style="font-size: 1.5rem; padding-left: 1.5rem;">{label}</p>',
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

    # Clean up resources after processing
    try:
        for temp_dir in ['pages', 'components', 'extracted_cells']:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception:
        pass  # Ignore cleanup errors

else:
    st.info('Please upload a PDF file to begin analysis')
    st.markdown("""
    ### Instructions

    **Step 1:** Upload a PDF file containing switchboard diagrams
    
    **Step 2:** Navigate through pages using the Previous/Next buttons
    
    **Step 3:** Review the identified components and their counts 
    """)
