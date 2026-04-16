import pypdfium2 as pdfium

def load_pdf(content:bytes):
    
    pdf_object = pdfium.PdfDocument(content)
    processed_contents = "\n".join(
        p.get_textpage().get_text_range() 
        for p in pdf_object
    ) 
    return processed_contents

