from pdf2image import convert_from_path
import os

def pdf_to_png(pdf_path, output_folder, dpi=72.2):
    # Convert PDF pages to images with specified DPI
    images = convert_from_path(pdf_path, dpi=dpi)
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save each page as a PNG file
    for i, image in enumerate(images):
        output_path = os.path.join(output_folder, f"page_{i+1}.png")
        image.save(output_path, 'PNG')
        print(f"Saved page {i+1} as {output_path}")

# Example usage
pdf_path = r'M6Doc\ocr (7).pdf'  # Replace with your PDF path
output_folder = r'M6Doc\BBOX_val'  # Replace with your output folder path
pdf_to_png(pdf_path, output_folder, dpi=72.2)
