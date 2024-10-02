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
import json
import ast
asterisk_added = {}
start_time = time.time()

class Center(Environment):
    packages = [Package('amsmath')]
    _latex_name = 'center'

def estimate_text_to_fit(hindi_text, bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size, bboxes):
    font_path = r"fonts\NotoSansMeeteiMayek-VariableFont_wght.ttf"
    
    font_sizes = [
        '\\veryHuge', '\\alphaa', '\\betaa', '\\gammaa', '\\deltaa', '\\epsilona', '\\veryhuge', '\\zetaa', '\\etaa', 
        '\\veryLarge', '\\iotaa', '\\kappaa', '\\verylarge', '\\lambdaa', '\\mua', '\\nua', '\\xia', '\\pia', 
        '\\Huge', '\\rhoa', '\\sigmaa', '\\huge', '\\taua', '\\upsilona', '\\LARGE', '\\phia', '\\Large', '\\chia', 
        '\\large', '\\psia', '\\normalsize', '\\small', '\\footnotesize', '\\ooomegaa', '\\scriptsize', 
        '\\omegaa', '\\tiny', '\\oomegaa', '\\oooomegaa'
    ]
    
    point_size = font_size_mapping.get(font_size, 12)
    font = ImageFont.truetype(font_path, point_size)

    img = Image.new('RGB', (int(bbox_width_inches * 72), int(bbox_height_inches * 72)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    words = hindi_text.split()
    random_start = random.randint(0, max(0, len(words) - 1))
    words = words[random_start:] + words[:random_start]
    
    truncated_text_lines = []
    truncated_text_with_linebreaks = []
    current_line = ''
    current_line_width = 0
    line_height = point_size
    line_height_2 = point_size + 5
    
    # Calculate the maximum number of lines that can fit in the bounding box
    max_lines = int(bbox_height_inches * 72 / line_height)

    # Add condition to check if max_lines is greater than 3
    if max_lines > 3:
        # Recalculate max_lines using line_height_2 if the condition is met
        max_lines = int(bbox_height_inches * 72 / line_height_2)

    for word in words:
        word_bbox = draw.textbbox((0, 0), word, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        space_bbox = draw.textbbox((0, 0), ' ', font=font)
        space_width = space_bbox[2] - space_bbox[0]
        new_line_width = current_line_width + space_width + word_width if current_line else word_width

        if new_line_width <= bbox_width_inches * 72:
            if current_line:
                current_line += ' ' + word
                current_line_width = new_line_width
            else:
                current_line = word
                current_line_width = word_width
        else:
            truncated_text_lines.append(current_line)
            truncated_text_with_linebreaks.append(current_line + r'\linebreak')
            current_line = word
            current_line_width = word_width

            # Stop adding lines if we've reached the max height
            if len(truncated_text_lines) >= max_lines:
                break

    if current_line and len(truncated_text_lines) < max_lines:
        truncated_text_lines.append(current_line)
        truncated_text_with_linebreaks.append(current_line + r'\linebreak') 



    if isinstance(bboxes, list):
        contains_footnote = any(bbox[4] == 'footnote' for bbox in bboxes)
        contains_paragraph = any(bbox[4] == 'paragraph' for bbox in bboxes)

        if contains_footnote and contains_paragraph:
            # print("Processing footnote or paragraph")

            # Find the current box
            current_box = next((bbox for bbox in bboxes if bbox[5] == box_id), None)
            if current_box:
                current_box_type = current_box[4]
                image_id = current_box[6]
                label_image_id = f"{current_box_type}:{image_id}"

                # print(f"Processing {label_image_id}")

                # Check if we need to add an asterisk
                if label_image_id not in asterisk_added:
                    if truncated_text_lines:
                        if current_box_type == 'footnote':
                            # Add asterisk to the beginning of the footnote
                            truncated_text_lines[0] = '*' + truncated_text_lines[0]
                            truncated_text_with_linebreaks[0] = truncated_text_lines[0] + r'\linebreak'
                            # print(f"Added '*' to the beginning of the footnote for {label_image_id}")
                        elif current_box_type == 'paragraph':
                            # Add asterisk to the end of the last line of the paragraph
                            last_line_idx = len(truncated_text_lines) - 1
                            words_in_last_line = truncated_text_lines[last_line_idx].split()
                            if words_in_last_line:
                                words_in_last_line[-1] += '*'
                                truncated_text_lines[last_line_idx] = ' '.join(words_in_last_line)
                                truncated_text_with_linebreaks[last_line_idx] = truncated_text_lines[last_line_idx] + r'\linebreak'
                                # print(f"Added '*' to the end of the last paragraph for {label_image_id}")
                    
                    # Mark that an asterisk has been added for this label:image_id
                    asterisk_added[label_image_id] = True
                else:
                    print(f"Asterisk already added for {label_image_id}. Skipping.")

                # print(f"Current state of asterisk_added: {asterisk_added}")


    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        annotations = data.get('annotations', [])
        box_id = int(box_id)
        updated = False
        max_line_idx = 0

        for annotation in annotations:
            if annotation['id'] == box_id:
                if 'textlines' in annotation and annotation['textlines']:
                    max_line_idx = max(line['line_idx'] for line in annotation['textlines']) + 1
                else:
                    annotation['text'] = ''
                    annotation['textlines'] = []

                for idx, line in enumerate(truncated_text_lines):
                    annotation['textlines'].append({
                        'line_idx': max_line_idx + idx,
                        'bbox': [x1, y1 + idx * line_height, bbox_width_inches * 72, line_height],
                        'text': line
                    })
                annotation['text'] += '\n'.join(truncated_text_lines)
                updated = True
                break

        if not updated:
            print(f"No annotation found with ID: {box_id}")

        with open(json_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            # print("JSON file saved successfully.")
    except Exception as e:
        print(f"Error processing JSON file: {e}")

    return '\n'.join(truncated_text_with_linebreaks[:max_lines])


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
    if (top_left == top_right) and (bottom_left == bottom_right) and (top_left != bottom_left):
        gradient_type = "vertical"
        start_color = top_left
        end_color = bottom_left

    elif (top_left == bottom_left) and (top_right == bottom_right) and (top_left != top_right):
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right

    elif (top_left != top_right) and (top_left != bottom_left) and (top_left != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal"
        start_color = top_left
        end_color = bottom_right

    elif (top_right != top_left) and (top_right != bottom_left) and (top_right != bottom_right) and (bottom_left != bottom_right):
        gradient_type = "diagonal_reverse"
        start_color = top_right
        end_color = bottom_left

    elif (top_left == top_right == bottom_left == bottom_right):
        gradient_type = "uniform"
        start_color = top_left
        end_color = top_left

    else:
        gradient_type = "horizontal"
        start_color = top_left
        end_color = top_right

    return gradient_type, start_color, end_color

def generate_latex_for_gradient(x1, y1, width, height, gradient_type, start_color, end_color):
    color1_latex = f"{start_color[0] / 255:.2f},{start_color[1] / 255:.2f},{start_color[2] / 255:.2f}"
    color2_latex = f"{end_color[0] / 255:.2f},{end_color[1] / 255:.2f},{end_color[2] / 255:.2f}"

    color1_name = f"color1_{x1}_{y1}"
    color2_name = f"color2_{x1}_{y1}"

    color_definitions = f"""
\\definecolor{{{color1_name}}}{{rgb}}{{{color1_latex}}}
\\definecolor{{{color2_name}}}{{rgb}}{{{color2_latex}}}
"""
    if gradient_type == "vertical":
        fill_command = f"\\shade[bottom color={{{color2_name}}}, top color={{{color1_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "horizontal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "diagonal_reverse":
        fill_command = f"\\shade[left color={{{color1_name}}}, right color={{{color2_name}}}, shading angle=-45] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"
    elif gradient_type == "uniform":
        fill_command = f"\\fill[{color2_name}] ({x1}pt,{y1}pt) rectangle ({x1 + width}pt,{y1 + height}pt);"

    return color_definitions + fill_command


def get_most_used_colors(image, bbox, n_colors=2):
    x1, y1, width, height = bbox[:4]
    patch = image.crop((x1, y1, x1 + width, y1 + height))
    patch_data = np.array(patch).reshape(-1, 3)
    color_counts = Counter(map(tuple, patch_data))
    most_common_colors = color_counts.most_common(n_colors)
    dominant_colors = [color for color, count in most_common_colors]
    return dominant_colors
    
def choose_text_color(bg_color, dominant_colors):
    tolerance = 10
    percentage_tolerance = 0.25
    black_color = np.array([0, 0, 0])
    bg_color = np.array(bg_color)
    dominant_colors = [np.array(color) for color in dominant_colors]
    
    def is_similar_color(color1, color2, tolerance, percentage_tolerance):
        abs_diff = np.abs(color1 - color2)
        relative_diff = abs_diff / 255.0 
        return np.all(relative_diff <= percentage_tolerance) or np.all(abs_diff <= tolerance)

    if not is_similar_color(dominant_colors[1], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[1]
    elif not is_similar_color(dominant_colors[0], bg_color, tolerance, percentage_tolerance):
        chosen_color = dominant_colors[0]
    else:
        chosen_color = black_color
    if is_similar_color(chosen_color, bg_color, tolerance, percentage_tolerance):
        return black_color
    
    return chosen_color

def rgb_to_normalized(rgb):
    return [val / 255.0 for val in rgb]

import os
import re

def extract_dimensions_and_text_from_file(image_path, file_path, hindi_text_file, label_mapping):
    try:
        # Read image dimensions from the first line
        with open(file_path, 'r') as file:
            image_dimensions_line = file.readline().strip()
            image_dimensions = eval(image_dimensions_line)  # Ensure this is safe (replace with safer parsing if needed)
            box_details = file.readlines()

            bboxes = []

            for line in box_details:
                if line.strip():
                    # Updated regex to match the new format: label, [x1, y1, width, height], annotation_id, image_id
                    match = re.match(r'^\[(.*?),\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\],\s*(\d+),\s*(\d+)\]$', line.strip())
                    if not match: 
                        print(f"Skipping malformed dumbitch line (regex match failed): {line.strip()}")
                        continue
                    
                    label = match.group(1).strip().strip('"')
                    dimensions = list(map(int, match.groups()[1:5]))  # Convert to integers
                    annotation_id = int(match.group(6))
                    image_id = int(match.group(7))  # Capture the image ID

                    if len(dimensions) == 4:
                        x1, y1, width, height = dimensions
                        # Append to bounding box list
                        bboxes.append([x1, y1, width, height, label, annotation_id, image_id])

        # Read Hindi texts
        hindi_texts = []
        with open(hindi_text_file, 'r', encoding='utf-8') as file:
            hindi_texts = file.read().splitlines()

        # Generate LaTeX code
        latex_code = generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping)

        # Prepare output folder and file paths
        base_path = 'Tex_files_label19'
        subfolder_name = os.path.splitext(os.path.basename(file_path))[0]
        output_folder = os.path.join(base_path, subfolder_name)
        os.makedirs(output_folder, exist_ok=True)

        # Save LaTeX file with image file name
        image_file_name = os.path.splitext(os.path.basename(image_path))[0]
        latex_output_file = os.path.join(output_folder, f"{image_file_name}.tex")
        with open(latex_output_file, "w", encoding='utf-8') as output_file:
            output_file.write(latex_code)

        # Uncomment to print confirmation if needed
        # print(f"LaTeX code has been written to {latex_output_file}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def get_bboxes_and_image_path(base_path):
    bbox_dir = os.path.join(base_path, 'ask')
    image_dir = os.path.join(base_path, 'images_val')
    json_dir = os.path.join(base_path, 'json_files')

    bbox_files_and_paths = []

    # Iterate through all subdirectories in bbox_dir
    for subdir, _, files in os.walk(bbox_dir):
        bbox_files = [f for f in files if f.endswith('.txt')]
        
        for bbox_file in bbox_files:
            bbox_file_path = os.path.join(subdir, bbox_file)

            # Derive the image file name from the bbox file name
            image_name = os.path.basename(bbox_file).replace('.txt', '.jpg')
            image_path = os.path.join(image_dir, image_name)
            
            if os.path.exists(image_path) and not os.path.basename(image_path).startswith('._'):
                # Derive the corresponding JSON file path
                json_file_path = os.path.join(json_dir, os.path.basename(bbox_file).replace('.txt', '.json'))

                if os.path.exists(json_file_path):
                    bbox_files_and_paths.append((bbox_file_path, image_path, json_file_path))

    if not bbox_files_and_paths:
        raise FileNotFoundError("No matching bounding box, image, or JSON file found.")

    return bbox_files_and_paths
   # Helper method for sentence splitting based on punctuation
def split_into_sentences(text):
    sentence_endings = re.compile(r'(?<=[.!?।])\s+')
    sentences = sentence_endings.split(text.strip())
    return sentences

def generate_latex(image_path, image_dimensions, bboxes, hindi_texts, label_mapping):
    doc = Document(documentclass='article')
    doc.packages.append(Package('tikz'))
    doc.packages.append(Package('fontspec'))
    doc.packages.append(NoEscape(r'\newfontfamily\hindifont[Script=Devanagari]{Teko-SemiBold.ttf}'))
    doc.packages.append(NoEscape(r'\newfontfamily\paragraphfont[Script=Devanagari]{TiroDevanagari-Regular.ttf}'))
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
    doc.append(NoEscape(r'\begin{center}'))
    doc.append(NoEscape(r'\begin{tikzpicture}[x=1pt, y=1pt]'))
    image_height, image_width = image_dimensions
    doc.append(NoEscape(f'\\node[anchor=south west, inner sep=0pt] at (0,0) {{\\includegraphics[width={image_width}pt,height={image_height}pt]{{{image_path}}}}};'))
    doc.append(NoEscape(f'\\node[anchor=east, rotate=90] at (-10pt, {image_height/2}pt) {{}};'))
    doc.append(NoEscape(r'\tikzset{hinditext/.style={font=\hindifont, text=black}}'))
    doc.append(NoEscape(r'\tikzset{paragraphtext/.style={font=\paragraphfont, text=black}}'))

    font_sizes = [
        '\\veryHuge', '\\alphaa', '\\betaa', '\\gammaa', '\\deltaa', '\\epsilona', '\\veryhuge', '\\zetaa', '\\etaa', '\\veryLarge', '\\iotaa', '\\kappaa', '\\verylarge',
        '\\lambdaa', '\\mua', '\\nua', '\\xia', '\\pia', '\\Huge', '\\rhoa', '\\sigmaa', '\\huge', '\\taua', '\\upsilona', '\\LARGE', '\\phia', '\\Large', '\\chia', '\\large', '\\psia', '\\normalsize', '\\small', 
        '\\footnotesize','\\ooomegaa', '\\scriptsize', '\\omegaa','\\tiny','\\oomegaa','\\oooomegaa', 
    ]

    image = Image.open(image_path).convert('RGB')
    padding_points = 5

    for bbox in bboxes:
        x1, y1, width, height, label, box_id,image_id = bbox
        ymin = image_height - (y1 + height)
        ymax = image_height - y1 
        xmin = x1
        xmax = x1 + width

        # Add padding only if the height is greater than 13 points
        if height > 26:
            width_with_padding = width - padding_points
            height_with_padding = height - padding_points
            ymin_with_padding = ymin + padding_points
            ymax_with_padding = ymax - padding_points
            xmin_with_padding = xmin + padding_points
            xmax_with_padding = xmax - padding_points

            if width_with_padding <= 0:
                width_with_padding = 0.01

            if height_with_padding <= 0:
                height_with_padding = 0.01
        else:
            width_with_padding = width - padding_points
            height_with_padding = height
            ymin_with_padding = ymin
            ymax_with_padding = ymax
            xmin_with_padding = xmin
            xmax_with_padding = xmax

        if (
            label not in ["figure_1", "formula_1","table", "formula", "QR code", "page number", "figure", "page_number", 
                        "mugshot", "code", "correlation", "bracket", "examinee info", "sealing line", 
                        "weather forecast", "barcode", "bill", "advertisement", "underscore", "blank", 
                        "other question number", "second-level question number", "third-level question number", 
                        "first-level question number"]
            # or re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower())
            # and not re.match(r'.*_2.*', label.lower())        
            ):

            bg_color = get_patch_color_with_gradient(image, bbox)
            gradient_type, start_color, end_color = bg_color
            latex_code = generate_latex_for_gradient(xmin, ymin, width, height, gradient_type, start_color, end_color)
            doc.append(NoEscape(latex_code))
        doc.append(NoEscape(f'\\draw[red] ({xmin},{ymin}) rectangle ({xmax},{ymax});'))
        # label_x = xmin 
        # label_y = ymax 
        # processed_label = label.replace(' ', '').replace('_', '')
        # doc.append(NoEscape(f'\\node[anchor=north west, text=black] at ({label_x},{label_y}) {{{{{processed_label}}}}};'))

        label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
        if isinstance(label_config, str):
            label_config = {"font_size": "\\Huge", "style": ""}
            
        font_size_command = label_config.get("font_size", "\\Huge")
        style_command = label_config.get("style", "")

        tikz_text_style = "paragraphtext" if label.lower().startswith("paragraph") or label.lower() == "answer" or label.lower() == "footnote"  or label.lower() == "Poem"  else "hinditext"
        bbox_width_inches = width_with_padding / 72.0
        bbox_height_inches = height_with_padding / 72.0


        if label not in ["figure_1","formula","formula_1","QR code","table","page number","figure", "page_number","mugshot","code","correlation","bracket","examinee info","sealing line","weather forecast","barcode","bill","advertisement","underscore","blank","other question number","second-level question number","third-level question number","first-level question number"]:
            if label.lower() == "dateline":
                def read_datelines(filename="datelines.txt"):
                    """Read the dateline.txt file and return a list of date lines."""
                    try:
                        with open(filename, 'r') as file:
                            datelines = [line.strip() for line in file.readlines()]
                            if not datelines:
                                print("No data lines found in the file.")
                            else:
                                print(f"Datelines read from file: {datelines}")
                        return datelines
                    except FileNotFoundError:
                        print(f"File {filename} not found.")
                        return []
                    except Exception as e:
                        print(f"An error occurred while reading the file: {e}")
                        return []

                datelines_list = read_datelines()
                selected_dateline = random.choice(datelines_list)
                doc.append(NoEscape(f'\\node[{tikz_text_style}, anchor=north west, text width={width_with_padding}pt] at ({xmin},{ymax+ 3.5}) {{{font_size_command} {style_command}{{{selected_dateline}}}}};'))

            if label.lower() in ["headline","author","credit","index"] and height > width:
                ymax = ymax + padding_points
                if x1 > (image_width / 2):
                    rotation = -90
                    anchor = "south west"
                    text_pos = f"({xmin},{ymax})"
                else:
                    rotation = 90
                    anchor = "north west"
                    text_pos = f"({xmin},{ymin})"

                label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Huge", "style": ""}
                font_size_command = label_config.get("font_size", "\\Huge")
                # print(font_size_command)
                style_command = label_config.get("style", "")   
                        
                hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_height_inches, bbox_width_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_height_inches, bbox_width_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            # print(font_size_command)
                            break

                doc.append(NoEscape(f'\\node[hinditext, anchor={anchor}, text width={height}pt,rotate={rotation}] at {text_pos} {{{font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'))
            elif label.lower() in ["ordered list", "unordered list", "catalogue", "option"]:
                label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
                
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Huge", "style": ""}

                font_size_command = label_config.get("font_size", "\\Huge")
                style_command = label_config.get("style", "")

                # Estimate text using the fitting function (line deletion handled in estimate_text_to_fit)
                estimated_text = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes)

                # Split the estimated text by \linebreak
                estimated_lines = estimated_text.split('\\linebreak')

                # Initialize the list format
                if label.lower() == "ordered list":
                    prefix_format = lambda idx: f"{idx + 1}. "  # Numbered list (1., 2., 3., ...)
                elif label.lower() == "unordered list":
                    prefix_format = lambda idx: "• "  # Bullet points (•)
                elif label.lower() == "option":
                    prefix_format = lambda idx: chr(65 + idx) + ". "  # Alphabetic options (A., B., C., ...)
                else:
                    prefix_format = lambda idx: ""  # Default (no prefix)

                # Add enumeration to each line, ensuring no extra enumeration after the last line
                enumerated_lines = [f"{prefix_format(idx)}{line.strip()}" for idx, line in enumerate(estimated_lines) if line.strip()]

                # Join all lines into a single string with \linebreak
                formatted_text = '\\linebreak'.join(enumerated_lines)

                # Print the formatted text for debugging purposes
                # print(formatted_text)

                # Generate the LaTeX code for a single node
                doc.append(NoEscape(
                    f'\\node[paragraphtext, anchor=north west, text width={bbox_width_inches * 72}pt, align=justify] at ({xmin},{ymax+3.5}) {{{font_size_command}{{{formatted_text}}}}};'
                ))

            elif (label.lower() not in ["index", "formula", "figure_1", "formula_1", "author_1", "dateline_1", "header", "headline", "subhead", "option", "figure", "credit", "dateline", "table_row1_col1", "table_row1_col2", "table_row1_col3"] 
                and not re.match(r'table_row[1-9][0-9]*_col[1-9][0-9]*', label.lower()) 
                or re.match(r'.*(?<!_1)_1$', label.lower())):
                
                # Check if label starts with "paragraph"
                if label.lower().startswith("paragraph") or label.lower() == "answer":
                    # If width is less than or equal to 70 points, skip this box
                    if width_with_padding <= 35:
                        continue  # Skip to the next bounding box
                    
                    # Otherwise, set alignment to 'justify'
                    alignment = 'justify'
                else:
                    alignment = 'left'

                label_config = label_mapping.get(label.lower(), {"font_size": "\\Huge", "style": ""})
                if isinstance(label_config, str):
                    label_config = {"font_size": "\\Huge", "style": ""}
                
                font_size_command = label_config.get("font_size", "\\Huge")
                style_command = label_config.get("style", "")
                hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes)
                # print(hindi_text_to_fit)
                if not hindi_text_to_fit:
                    for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                        hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches, box_id, json_file_path, x1, y1, font_size_command,bboxes)
                        if hindi_text_to_fit:
                            font_size_command = font_size
                            # print(font_size_command)
                            break
                
                if hindi_text_to_fit:
                    doc.append(NoEscape(
                        f'\\node[{tikz_text_style}, anchor=north west, text width={width_with_padding}pt, align={alignment}] at ({xmin},{ymax+ 3.5}) {{{font_size_command} {style_command}{{{hindi_text_to_fit}}}}};'
                    ))


        if label in ["header","headline", "subhead","credit","section"] and height < width:
            # print("header was there")
            label_config = label_mapping.get(label.lower(), {"font_size": "", "style": ""})
            if isinstance(label_config, str):
                label_config = {"font_size": "", "style": ""}
            font_size_command = label_config.get("font_size", "\\Huge")
            style_command = label_config.get("style", "")
            hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
            # print(hindi_text_to_fit)

            if not hindi_text_to_fit:
                # print("no hindi_text")
                for font_size in font_sizes[font_sizes.index(font_size_command) + 1:]:
                    hindi_text_to_fit = estimate_text_to_fit(' '.join(hindi_texts), bbox_width_inches, bbox_height_inches,box_id,json_file_path, x1, y1, font_size_command,bboxes)
                    # print(hindi_text_to_fit)
                    # print(font_size)
                    if hindi_text_to_fit:
                        font_size_command = font_size
                        # print(font_size_command)
                        break

            if hindi_text_to_fit:
                dominant_colors = get_most_used_colors(image, bbox)
                text_color = choose_text_color(start_color, dominant_colors)
                text_color_normalized = rgb_to_normalized(text_color)
                normalized_color_str = ','.join(map(str, text_color_normalized))
                r, g, b = normalized_color_str.split(',')
                color_str = f'text={{rgb,1:red,{r};green,{g};blue,{b}}}'
                doc.append(NoEscape(
                    f'\\node[{tikz_text_style}, anchor=north west, text width={width_with_padding}pt, {color_str}]'
                    f'at ({xmin},{ymax+ 3.5}) '
                    f'{{{font_size_command} {style_command} {hindi_text_to_fit}}};'
                ))
    doc.append(NoEscape(r'\end{tikzpicture}'))
    doc.append(NoEscape(r'\end{center}'))
    return doc.dumps()

font_size_mapping = {
    '\\tiny': 5, '\\scriptsize': 7, '\\footnotesize': 8, '\\small': 9, '\\normalsize': 10,
    '\\large': 12, '\\Large': 15, '\\LARGE': 17, '\\huge': 20, '\\Huge': 25, '\\verylarge': 37,
    '\\veryLarge': 43, '\\veryhuge': 49, '\\veryHuge': 62, '\\alphaa': 60, '\\betaa': 57,
    '\\gammaa': 55, '\\deltaa': 53, '\\epsilona': 51, '\\zetaa': 47, '\\etaa': 45,
    '\\iotaa': 41, '\\kappaa': 39, '\\lambdaa': 35, '\\mua': 33, '\\nua': 31,
    '\\xia': 29, '\\pia': 27, '\\rhoa': 24, '\\sigmaa': 22, '\\taua': 18,
    '\\upsilona': 16, '\\phia': 15, '\\chia': 13, '\\psia': 11, '\\omegaa': 6,
    '\\oomegaa': 4, '\\ooomegaa': 3, '\\oooomegaaa': 2
}
def read_bboxes_from_file(file_path):
    bboxes = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                # Adjusted regex pattern to correctly parse the label and bounding box details
                match = re.match(r'^\[(.*?),\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\],\s*(\d+),\s*(\d+)\]$', line)
                if not match:
                    print(f"Skipping malformed read bboxes line (regex match failed): {line}")
                    continue

                label = match.group(1).strip().strip('"')
                bbox_values = [int(match.group(i)) for i in range(2, 6)]  # x1, y1, width, height
                annotation_id = int(match.group(6))
                image_id = int(match.group(7))

                # Append the extracted values as a tuple
                bboxes.append((label, bbox_values, annotation_id, image_id))
            except Exception as e:
                print(f"Error processing line '{line}': {e}")
    
    return bboxes


def find_closest_font_size(height, font_size_mapping):
    """Find the closest font size based on the adjusted height, ensuring it's less than or equal to the height."""
    adjusted_height = height
    valid_sizes = {size: value for size, value in font_size_mapping.items() if value <= adjusted_height}
    if not valid_sizes:
        return None
    return min(valid_sizes, key=lambda size: abs(font_size_mapping[size] - adjusted_height))

def set_uniform_font_size_for_labels(bboxes, font_size_mapping):
    """Set a uniform font size for both 'paragraph' and 'answer' bounding boxes based on the smallest height.
       If the min height is greater than 15pts, the font size is set to 'Large'."""

    min_height = float('inf')

    # Find the minimum height among all 'paragraph' and 'answer' bounding boxes
    for label, coords, bbox_id, _ in bboxes:  # Adjusted to unpack the new format
        if label.startswith("paragraph") or label.startswith("answer"):
            height = coords[3]  # Height is the 4th value in the list
            if height < min_height:
                min_height = height

    if min_height == float('inf'):
        print("No 'paragraph' or 'answer' bounding boxes found.")
        return None

    # Check if the minimum height is greater than 15pts
    if min_height >= 20:
        return "\\huge"  # Set to 'Large' if the minimum height is greater than 15pts

    # Find the closest font size for the adjusted height if min height is <= 15pts
    closest_font_size = find_closest_font_size(min_height, font_size_mapping)
    
    if closest_font_size:
        print(f"Uniform font size for all 'paragraph' and 'answer' bounding boxes: {closest_font_size}")
    else:
        print("No suitable font size found.")

    return closest_font_size

label_mapping = {
    "section": {"font_size": "\\huge", "style": ""},
    "byline": {"font_size": "\\small", "style": ""},
    "breakout": {"font_size": "\\Large", "style": ""},
    "dropcap": {"font_size": "\\Huge", "style": ""},
    "caption": {"font_size": "\\footnotesize", "style": ""},
    "jump-line": {"font_size": "\\footnotesize", "style": ""},
    "subhead": {"font_size": "\\Large", "style": ""},
    "credit": {"font_size": "\\scriptsize", "style": ""},
    "advertisement": {"font_size": "\\small", "style": ""},
    "answer": {"font_size": "\\normalsize", "style": ""},
    "author": {"font_size": "\\small", "style": ""},
    "chapter-title": {"font_size": "\\Huge", "style": ""},
    "contact-info": {"font_size": "\\small", "style": ""},
    "dateline": {"font_size": "\\footnotesize", "style": ""},
    "figure": "figure",
    "figure-caption": {"font_size": "\\footnotesize", "style": ""},
    "first-level-question": {"font_size": "\\large", "style": ""},
    "flag": {"font_size": "\\Huge", "style": ""},
    "folio": {"font_size": "\\scriptsize", "style": ""},
    "footnote": {"font_size": "\\scriptsize", "style": ""},
    "formula": {"font_size": "\\normalsize", "style": ""},
    "headline": {"font_size": "\\Huge", "style": ""},
    "header": {"font_size": "\\Large", "style": ""},
    "index": {"font_size": "\\normalsize", "style": ""},
    "jumpline": {"font_size": "\\footnotesize", "style": ""},
    "question": {"font_size": "\\normalsize", "style": ""},
    "option": {"font_size": "\\normalsize", "style": ""},
    "ordered-list": {"font_size": "\\normalsize", "style": ""},
    "page_number": {"font_size": "\\small", "style": ""},
    "paragraph": {"font_size": "\\chia", "style": ""},
    "answer": {"font_size": "\\chia", "style": ""},
    "paragraph_1": {"font_size": "", "style": ""},
    "placeholder-text": {"font_size": "\\small", "style": ""},
    "reference": {"font_size": "\\footnotesize", "style": ""},
    "sub_section_title": {"font_size": "\\Large", "style": ""},
    "sidebar": {"font_size": "\\small", "style": ""},
    "sub-headline": {"font_size": "\\large", "style": ""},
    "sub-section-title": {"font_size": "\\large", "style": ""},
    "subsub-section-title": {"font_size": "\\normalsize", "style": ""},
    "table": {"font_size": "\\footnotesize", "style": ""},
    "table-caption": {"font_size": "\\footnotesize", "style": ""},
    "table-of-contents": {"font_size": "\\Large", "style": ""},
    "unordered list": {"font_size": "\\Large", "style": ""},
    "ordered list": {"font_size": "\\Large", "style": ""}
}


# Example usage
hindi_text_file = r"M6Doc\hind_text_file.txt"
base_path = 'M6Doc'
bbox_files_and_paths = get_bboxes_and_image_path(base_path)

for bbox_file_path, image_path, json_file_path in bbox_files_and_paths:
    bboxes = read_bboxes_from_file(bbox_file_path)
    # print(f"Bounding boxes read: {bboxes}")  # Debugging print
    uniform_font_size = set_uniform_font_size_for_labels(bboxes, font_size_mapping)
    if uniform_font_size:
    # Update the label_mapping dictionary
        label_mapping["paragraph"]["font_size"] = uniform_font_size
        # print(f"Updated 'paragraph' font size to: {uniform_font_size}")
    # else:
    #     print("No font size updated for 'paragraph'.")
    extract_dimensions_and_text_from_file(image_path, bbox_file_path, hindi_text_file, label_mapping)

end_time = time.time()
execution_time = end_time - start_time
print(f"Execution Time: {execution_time} seconds")