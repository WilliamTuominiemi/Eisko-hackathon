import streamlit as st
from pdf2image import convert_from_path
import tempfile
import os
from PIL import Image

st.set_page_config(page_title="PDF to Image Converter", page_icon="📄")

st.title("📄 PDF to Image Converter")
st.write("Upload a PDF file and convert any page to an image")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

if uploaded_file is not None:
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    try:
        # Get total number of pages
        from pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(tmp_path)
        total_pages = info['Pages']
        
        st.success(f"PDF uploaded successfully! Total pages: {total_pages}")
        
        # Page selector
        page_number = st.number_input(
            "Select page to convert",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )
        
        # DPI selector
        dpi = st.slider("Select image quality (DPI)", min_value=72, max_value=300, value=150, step=10)
        
        # Convert button
        if st.button("Convert to Image", type="primary"):
            with st.spinner(f"Converting page {page_number}..."):
                # Convert the selected page to image
                images = convert_from_path(
                    tmp_path,
                    first_page=page_number,
                    last_page=page_number,
                    dpi=dpi
                )
                
                if images:
                    st.success("Conversion completed!")
                    
                    # Display the image
                    st.image(images[0], caption=f"Page {page_number}", use_container_width=True)
                    
                    # Option to download the image
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                        images[0].save(tmp_img.name, 'JPEG')
                        with open(tmp_img.name, 'rb') as img_file:
                            st.download_button(
                                label="Download Image",
                                data=img_file.read(),
                                file_name=f"page_{page_number}.jpg",
                                mime="image/jpeg"
                            )
                        os.unlink(tmp_img.name)
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

else:
    st.info("👆 Please upload a PDF file to get started")
    
    # Show example usage
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        1. Upload a PDF file using the file uploader above
        2. Select which page you want to convert to an image
        3. Adjust the DPI (quality) if needed
        4. Click "Convert to Image" to see the result
        5. Download the image if you want to save it
        """)

