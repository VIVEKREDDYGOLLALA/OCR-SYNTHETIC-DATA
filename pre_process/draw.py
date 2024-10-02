import textwrap
import random
import requests
from io import BytesIO
import time
from pylatex import Document, NoEscape, Package
from pylatex.base_classes import Environment
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import os
import re


start_time = time.time()

class Center(Environment):
    packages = [Package('amsmath')]
    _latex_name = 'center'


def estimate_text_to_fit(hindi_text, bbox_width_inches, bbox_height_inches, font_size='\\footnotesize'):
    # Path to the font file
    font_path = "fonts\TiroDevanagari-Regular.ttf"  # Replace with actual path to the Devanagari font

    # Custom font size mapping corresponding to your LaTeX commands
    font_size_mapping = {
        '\\tiny': 5,
        '\\scriptsize': 7,
        '\\footnotesize': 8,
        '\\small': 9,
        '\\normalsize': 10,
        '\\large': 12,
        '\\Large': 14,
        '\\LARGE': 17,
        '\\huge': 20,
        '\\Huge': 25,
        '\\verylarge': 37,
        '\\veryLarge': 43,
        '\\veryhuge': 49,
        '\\veryHuge': 62,
        '\\alphaa': 60,
        '\\betaa': 57,
        '\\gammaa': 55,
        '\\deltaa': 53,
        '\\epsilona': 51,
        '\\zetaa': 47,
        '\\etaa' : 45,
        '\\iotaa': 41,
        '\\kappaa': 39,
        '\\lambdaa': 35,
        '\\mua': 33,
        '\\nua': 31,
        '\\xia': 29,
        '\\pia': 27,
        '\\rhoa': 24,
        '\\sigmaa': 22,
        '\\taua': 18,
        '\\upsilona': 16,
        '\\phia': 15,
        '\\chia': 13,
        '\\psia': 11,
        '\\omegaa': 6,
        '\\oomegaa': 4,
        '\\ooomegaa': 3,
        '\\oooomegaaa': 2
    }

    # Map the font size string to a point size
    point_size = font_size_mapping.get(font_size, 12)
    font = ImageFont.truetype(font_path, point_size)

    # Create an image to draw text on
    img = Image.new('RGB', (int(bbox_width_inches * 72), int(bbox_height_inches * 72)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Split the text into words
    words = hindi_text.split()
    
    # Introduce a random starting index
    random_start = random.randint(0, max(0, len(words) - 1))
    words = words[random_start:] + words[:random_start]
    
    truncated_text_lines = []
    current_line = ''
    current_line_width = 0

    line_height = point_size + 2  # Adjust line height based on point size

    for word in words:
        word_bbox = draw.textbbox((0, 0), word, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        space_bbox = draw.textbbox((0, 0), ' ', font=font)
        space_width = space_bbox[2] - space_bbox[0]

        if current_line:
            new_line_width = current_line_width + space_width + word_width
        else:
            new_line_width = word_width

        if new_line_width <= bbox_width_inches * 72:
            if current_line:
                current_line += ' ' + word
                current_line_width = new_line_width
            else:
                current_line = word
                current_line_width = word_width
        else:
            truncated_text_lines.append(current_line)
            current_line = word
            current_line_width = word_width

            if len(truncated_text_lines) >= int(bbox_height_inches * 72 / line_height):
                break

    if current_line and len(truncated_text_lines) < int(bbox_height_inches * 72 / line_height):
        truncated_text_lines.append(current_line)

    return '\n'.join(truncated_text_lines[:int(bbox_height_inches * 72 / line_height)])

def get_patch_color_with_gradient(image, bbox):
    x1, y1, width, height = bbox[:4]
    corners = [
        (x1, y1),
        (x1 + width - 2, y1),
        (x1, y1 + height - 2),
        (x1 + width - 2, y1 + height - 2)
    ]

    corner_colors = [image.getpixel(corner) for corner in corners]

    top_left, top_right, bottom_left, bottom_right = corner_colors

    # Case 1: Vertical Gradient
    if (top_left == top_right) and (bottom_left == bottom_right) and (top_left != bottom_left):
        gradient_type = "vertical"
        start_color = top_left
        end_color = bottom_left

    # Case 2: Horizontal Gradient
    elif (top_left == bottom_left) and (top_right == bottom_right) and (top_left != top_right):
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right

    # Case 3: Diagonal Gradient (top-left to bottom-right)
    elif (top_left != top_right) and (top_left != bottom_left) and (top_left != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal"
        start_color = top_left
        end_color = bottom_right

    # Case 4: Diagonal Gradient (top-right to bottom-left)
    elif (top_right != top_left) and (top_right != bottom_left) and (top_right != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal_reverse"
        start_color = top_right
        end_color = bottom_left

    # Case 5: Uniform Color
    elif (top_left == top_right == bottom_left == bottom_right):
        gradient_type = "uniform"
        start_color = top_left
        end_color = top_left

    # Default case: horizontal gradient
    else:
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right

    return gradient_type, start_color, end_color

def generate_latex_for_gradient(x1, y1, width, height, gradient_type, start_color, end_color):
    # Convert RGB color values to LaTeX color format
    color1_latex = f"{start_color[0] / 255:.2f},{start_color[1] / 255:.2f},{start_color[2] / 255:.2f}"
    color2_latex = f"{end_color[0] / 255:.2f},{end_color[1] / 255:.2f},{end_color[2] / 255:.2f}"

    color1_name = f"color1_{x1}_{y1}"
    color2_name = f"color2_{x1}_{y1}"

    # Define colors using \definecolor
    color_definitions = f"""
\\definecolor{{{color1_name}}}{{rgb}}{{{color1_latex}}}
\\definecolor{{{color2_name}}}{{rgb}}{{{color2_latex}}}
"""

    # Define gradient fill command
    if gradient_type == "vertical":
        fill_command = f"\\shade[bottom color={{{color2_name}}}, top color={{{color1_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "horizontal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal_reverse":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=-45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "uniform":  # Default to uniform color fill
        fill_command = f"\\fill[{color2_name}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"

    return color_definitions + fill_command


def get_most_used_colors(image, bbox, n_colors=2):
    x1, y1, width, height = bbox[:4]
    patch = image.crop((x1, y1, x1 + width, y1 + height))
    patch_data = np.array(patch).reshape(-1, 3)

    # Count the occurrences of each color
    color_counts = Counter(map(tuple, patch_data))
    
    # Get the n most common colors
    most_common_colors = color_counts.most_common(n_colors)
    
    # Extract just the colors
    dominant_colors = [color for color, count in most_common_colors]
    return dominant_colors
    
def choose_text_color(bg_color, dominant_colors):
    tolerance = 10
    percentage_tolerance = 0.25  # 50 percent similarity
    black_color = np.array([0, 0, 0])
    
    # Convert input colors to numpy arrays
    bg_color = np.array(bg_color)
    dominant_colors = [np.array(color) for color in dominant_colors]
    
    def is_similar_color(color1, color2, tolerance, percentage_tolerance):
        abs_diff = np.abs(color1 - color2)
        relative_diff = abs_diff / 255.0  # Normalize the difference
        return np.all(relative_diff <= percentage_tolerance) or np.all(abs_diff <= tolerance)

    if not is_similar_color(dominant_colors[1], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[1]
    elif not is_similar_color(dominant_colors[0], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[0]
    else:
        chosen_color = black_color

    # Check if the chosen color is close to the background color
    if is_similar_color(chosen_color, bg_color, tolerance, percentage_tolerance):
        return black_color
    
    return chosen_color

def rgb_to_normalized(rgb):
    return [val / 255.0 for val in rgb]

def extract_dimensions_and_text_from_file(image_path, file_path, hindi_text_file, label_mapping):
    try:
        # Read image dimensions and bounding box details from file
        with open(file_path, 'r') as file:
            image_dimensions_line = file.readline().strip()
            image_dimensions = eval(image_dimensions_line)
            box_details = file.readlines()

            bboxes = []

            for line in box_details:
                if line.strip():
                    # Remove brackets and split by commas
                    parts = line.strip().strip("[]").split("],")
                    label_and_dimensions = parts[0].strip().split(",")
                    
                    # Extract label and dimensions
                    label = label_and_dimensions[0].strip().strip('"')
                    dimensions_str = ','.join(label_and_dimensions[1:]).replace('[', '').replace(']', '')
                    dimensions = list(map(float, dimensions_str.split(',')))
                    
                    # Extract annotation ID
                    annotation_id = parts[1].strip()
                    
                    # Check if dimensions are valid
                    if len(dimensions) == 4:
                        x1, y1, width, height = dimensions
                        bboxes.append([x1, y1, width, height, label, annotation_id])

        # Read Hindi texts
        hindi_texts = []
        with open(hindi_text_file, 'r', encoding='utf-8') as file:
            hindi_texts = file.read().splitlines()

        # Generate LaTeX code
        latex_code = generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping)

        # Write LaTeX code to output file
        latex_output_file = "boxes.tex"
        with open(latex_output_file, "w", encoding='utf-8') as output_file:
            output_file.write(latex_code)

        print(f"LaTeX code has been written to {latex_output_file}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

def get_bboxes_and_image_path(document_category):
    base_path = r"M6Doc"
    if document_category == "00":
        bbox_dir = os.path.join(base_path, r"BBOX_val\00")
    elif document_category == "books":
        bbox_dir = os.path.join(base_path, r"BBOX_val\books")
    elif document_category == "newspaper":
        bbox_dir = os.path.join(base_path, r"BBOX_val\newspaper")
    elif document_category == "magazines":
        bbox_dir = os.path.join(base_path, r"BBOX_val\magazines")
    elif document_category == "scientific_articles":
        bbox_dir = os.path.join(base_path, r"BBOX_val\scientific_articles")
    elif document_category == "Form":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Form")
    elif document_category == "Brochure, Posters and Leaflets":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Brochure_Posters_Leaflets")
    elif document_category == "Acts and Rules":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Acts_and_Rules")
    elif document_category == "Notice":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Notice")
    elif document_category == "Syllabus":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Syllabus")
    elif document_category == "question_paper":
        bbox_dir = os.path.join(base_path, r"BBOX_val\question_paper")
    elif document_category == "Manual":
        bbox_dir = os.path.join(base_path, r"BBOX_val\Manual")
    else:
        raise ValueError(f"Unsupported document category: {document_category}")


    # List all bbox files
    bbox_files = [os.path.join(bbox_dir, f) for f in os.listdir(bbox_dir) if f.endswith('.txt')]
    if not bbox_files:
        raise FileNotFoundError("No bounding box files found for the selected document category")

    for bbox_file in bbox_files:
        image_name = os.path.basename(bbox_file).replace('.txt', '.jpg')
        image_path = os.path.join(base_path, r"images_val", image_name)

        if not os.path.basename(image_path).startswith('._') and os.path.exists(image_path):
            return bbox_file, image_path

    raise FileNotFoundError("No valid images found for the bounding box files")

def generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping):
    doc = Document(documentclass='article')
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('fontspec'))
    doc.packages.append(NoEscape(r'\newfontfamily\hindifont[Script=Devanagari]{Teko-SemiBold.ttf}'))
    doc.packages.append(NoEscape(r'\newfontfamily\paragraphfont[Script=Devanagari]{TiroDevanagariHindi-Regular.ttf}'))
    doc.packages.append(Package('geometry', options=f'paperwidth={image_dimensions[1]}pt,paperheight={image_dimensions[0]}pt,margin=0pt'))
    doc.append(NoEscape(r'''

    \makeatletter
    \newcommand{\verylarge}{\@setfontsize\verylarge{37}{42}}
    \newcommand{\veryLarge}{\@setfontsize\veryLarge{43}{49}}
    \newcommand{\veryhuge}{\@setfontsize\veryhuge{49}{55}}
    \newcommand{\veryHuge}{\@setfontsize\veryHuge{62}{70}}
    \newcommand{\alphaa}{\@setfontsize\alphaa{60}{66}}
    \newcommand{\betaa}{\@setfontsize\betaa{57}{63}}
    \newcommand{\gammaa}{\@setfontsize\gammaa{55}{61}}
    \newcommand{\deltaa}{\@setfontsize\deltaa{53}{59}}
    \newcommand{\epsilona}{\@setfontsize\epsilona{51}{57}}
    \newcommand{\zetaa}{\@setfontsize\zetaa{47}{53}}
    \newcommand{\etaa}{\@setfontsize\etaa{45}{51}}
    \newcommand{\iotaa}{\@setfontsize\iotaa{41}{47}}
    \newcommand{\kappaa}{\@setfontsize\kappaa{39}{45}}
    \newcommand{\lambdaa}{\@setfontsize\lambdaa{35}{41}}
    \newcommand{\mua}{\@setfontsize\mua{33}{39}}
    \newcommand{\nua}{\@setfontsize\nua{31}{37}}
    \newcommand{\xia}{\@setfontsize\xia{29}{35}}
    \newcommand{\pia}{\@setfontsize\pia{27}{33}}
    \newcommand{\rhoa}{\@setfontsize\rhoa{24}{30}}
    \newcommand{\sigmaa}{\@setfontsize\sigmaa{22}{28}}
    \newcommand{\taua}{\@setfontsize\taua{18}{24}}
    \newcommand{\upsilona}{\@setfontsize\upsilona{16}{22}}
    \newcommand{\phia}{\@setfontsize\phia{15}{20}}
    \newcommand{\chia}{\@setfontsize\chia{13}{18}}
    \newcommand{\psia}{\@setfontsize\psia{11}{16}}
    \newcommand{\omegaa}{\@setfontsize\omegaa{6}{7}}
    \newcommand{\oomegaa}{\@setfontsize\oomegaa{4}{5}}
    \newcommand{\ooomegaa}{\@setfontsize\ooomegaa{3}{4}}
    \newcommand{\oooomegaaa}{\@setfontsize\oooomegaaa{2}{3}}
    \makeatother
    '''))

    doc.append(NoEscape(r'\begin{document}'))
    doc.append(NoEscape(r'\begin{center}'))
    doc.append(NoEscape(r'\begin{tikzpicture}[x=1pt, y=1pt]'))

    image_height, image_width = image_dimensions
    doc.append(NoEscape(f'\\node[anchor=south west, inner sep=0pt] at (0,0) {{\\includegraphics[width={image_width}pt,height={image_height}pt]{{{image_path}}}}};'))
    doc.append(NoEscape(f'\\node[anchor=north] at ({image_width/2}pt, {image_height + 10}pt) {{}};'))
    doc.append(NoEscape(f'\\node[anchor=east, rotate=90] at (-10pt, {image_height/2}pt) {{}};'))
    doc.append(NoEscape(r'\tikzset{hinditext/.style={font=\hindifont, text=black}}'))
    doc.append(NoEscape(r'\tikzset{paragraphtext/.style={font=\paragraphfont, text=black}}'))

    font_sizes = [
        '\\veryHuge', '\\alphaa', '\\betaa', '\\gammaa', '\\deltaa', '\\epsilona', '\\veryhuge', '\\zetaa', '\\etaa', '\\veryLarge', '\\iotaa', '\\kappaa', '\\verylarge',
        '\\lambdaa', '\\mua', '\\nua', '\\xia', '\\pia', '\\Huge', '\\rhoa', '\\sigmaa', '\\huge', '\\taua', '\\upsilona', '\\LARGE', '\\phia', '\\Large', '\\chia', '\\large', '\\psia', '\\normalsize', '\\small', 
        '\\footnotesize','\\ooomegaa', '\\scriptsize', '\\omegaa','\\tiny','\\oomegaa','\\oooomegaa', 
    ]

    image = Image.open(image_path).convert('RGB')
    padding_points = 5  # Padding in points (adjust as needed)

    for bbox in bboxes:
        x1, y1, width, height, label,box_id = bbox
        ymin = image_height - (y1 + height)
        ymax = image_height - y1
        xmin = x1
        xmax = x1 + width

        width_with_padding = width - 2 * padding_points
        height_with_padding = height - 2 * padding_points
        ymin_with_padding = ymin + padding_points
        ymax_with_padding = ymax - padding_points
        xmin_with_padding = xmin + padding_points
        xmax_with_padding = xmax - padding_points
        doc.append(NoEscape(f'\\draw[green] ({xmin},{ymin}) rectangle ({xmax},{ymax});'))
        label_x = xmin  # Left X
        label_y = ymax  # Top Y

        processed_label = label.replace(' ', '').replace('_', '')
        doc.append(NoEscape(f'\\node[anchor=north west, text=black] at ({label_x},{label_y}) {{\\textbf{{{processed_label}}}}};'))

    doc.append(NoEscape(r'\end{tikzpicture}'))
    doc.append(NoEscape(r'\end{center}'))
    doc.append(NoEscape(r'\end{document}'))
    return doc.dumps()

label_mapping = {

    "section": {"font_size": "\\veryLarge", "style": "\\textit"},
    "byline": {"font_size": "\\veryLarge", "style": "\\textit"},
    "breakout": {"font_size": "\\veryHuge", "style": "\\textbf{\\Huge\\color{red}"},
    "caption": {"font_size": "\\veryLarge", "style": "\\textit"},
    "jump-line": {"font_size": "\\veryLarge", "style": "\\textit"},
    "subhead": {"font_size": "\\veryLarge", "style": "\\textbf\\Huge"},
    "credit": {"font_size": "\\tiny", "style": "\\textit"},
    "advertisement": {"font_size": "\\footnotesize", "style": "\\textit"},
    "answer": {"font_size": "\\scriptsize", "style": "\\textbf"},
    "author": {"font_size": "\\small", "style": "\\textit"},
    "chapter-title": {"font_size": "\\veryHuge", "style": "\\textbf"},
    "contact-info": {"font_size": "\\veryLarge", "style": "\\textit"},
    "dateline": {"font_size": "\\veryLarge", "style": "\\textit"},
    "figure": "figure",
    "figure-caption": {"font_size": "\\veryLarge", "style": "\\textbf"},
    "first-level-question": {"font_size": "\\Large", "style": "\\textbf"},
    "flag": {"font_size": "\\veryLarge", "style": "\\textit"},
    "folio": {"font_size": "\\veryLarge", "style": "\\textit"},
    "footnote": {"font_size": "\\veryLarge", "style": "\\textit"},
    "formula": {"font_size": "\\large", "style": "\\textit"},
    "headline": {"font_size": "\\Huge", "style": "\\textbf\\Huge"},
    "header": {"font_size": "\\veryHuge", "style": "\\textbf\\Huge"},
    "index": {"font_size": "\\small", "style": "\\textbf"},
    "jumpline": {"font_size": "\\footnotesize", "style": "\\textit"},
    "question": {"font_size": "\\normalsize", "style": "\\textbf"},
    "option": {"font_size": "\\large", "style": "\\textbf"},
    "ordered-list": {"font_size": "\\normalsize", "style": "\\textit"},
    "page_number": {"font_size": "\\veryHuge", "style": "\\textbf"},
    "paragraph": {"font_size": "\\Huge", "style": ""},
    "placeholder-text": {"font_size": "\\small", "style": "\\textit"},
    "reference": {"font_size": "\\small", "style": "\\textit"},
    "sub_section_title": {"font_size": "\\huge", "style": "\\textbf"},
    "sidebar": {"font_size": "\\footnotesize", "style": "\\textit"},
    "sub-headline": {"font_size": "\\veryHuge", "style": "\\textbf"},
    "sub-section-title": {"font_size": "\\Large", "style": "\\textbf"},
    "subsub-section-title": {"font_size": "\\large", "style": "\\textbf"},
    "table": {"font_size": "\\footnotesize", "style": ""},
    "table-caption": {"font_size": "\\footnotesize", "style": "\\textit"},
    "table-of-contents": {"font_size": "\\huge", "style": "\\textbf"},
    "unordered-list": {"font_size": "\\normalsize", "style": "\\textit"}
}

hindi_text_file = r"M6Doc\hind_text_file.txt"
document_category = input("Enter document category (e.g., newspaper): ").strip().lower()
file_path, image_path = get_bboxes_and_image_path(document_category)
print(file_path)
print(image_path)

extract_dimensions_and_text_from_file(image_path,file_path, hindi_text_file, label_mapping)

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution Time: {execution_time} seconds")