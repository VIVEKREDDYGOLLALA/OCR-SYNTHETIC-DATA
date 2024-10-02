import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def show_image(image_path, new_width=None, new_height=None):
    # Load the image using PIL
    img = Image.open(image_path)
    
    # Print the original image dimensions
    original_width, original_height = img.size
    print(f"Original Image Dimensions: {original_width}x{original_height}")
    
    # Resize the image if new dimensions are provided
    if new_width and new_height:
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"Resized Image Dimensions: {new_width}x{new_height}")
    
    # Convert the PIL image to a NumPy array for matplotlib
    img = np.array(img)

    # Create a figure and axis
    fig, ax = plt.subplots()

    # Display the image on the axis
    ax.imshow(img)

    # Optionally hide the axes
    ax.axis('on')

    # Show the plot
    plt.show()

# Example usage
image_path = r'M6Doc\BBOX_val\page_2.png'  # Replace with your image path
show_image(image_path)  # Adjust width and height as needed
