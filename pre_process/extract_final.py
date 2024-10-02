import os
import json
import shutil
import os
import re

base_folder = r'M6Doc\BBOX_val'
base_folder_2 = r'M6Doc\BBOX_val' 
json_file_path = r'M6Doc\input_jsons\instances_val2017.json'
input_folder = r'M6Doc\BBOX_val'
base_folder_3 = r'M6Doc\BBOX_val'  

def create_folders_and_save_bbox(json_file, input_folder):
    # Load the JSON data with utf-8 encoding
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Create a dictionary to map image ids to their details
    image_dict = {img['id']: img for img in data['images']}
    
    # Create a dictionary to map category ids to their names
    category_dict = {cat['id']: cat['name'] for cat in data['categories']}
    
    processed_files = set()

    # Define the base output directory
    base_folder = os.path.join('M6Doc')
    os.makedirs(base_folder, exist_ok=True)  # Create the directory if it doesn't exist

    # Process each annotation
    for annotation in data['annotations']:
        image_id = annotation['image_id']
        bbox = annotation['bbox']
        category_id = annotation['category_id']
        image_info = image_dict[image_id]
        image_height = image_info['height']
        image_width = image_info['width']
        file_name = image_info['file_name']

        # Use 'doc_name' if it exists, otherwise use a default value
        doc_name = image_info.get('doc_name', 'BBOX_val')
        
        # Create a folder named after the doc_name (if it doesn't exist)
        folder_path = os.path.join(base_folder, doc_name)
        os.makedirs(folder_path, exist_ok=True)

        # Create a text file with the name formatted as filename_image_id (with .txt extension)
        bbox_file_path = os.path.join(folder_path, f"{file_name.rsplit('.', 1)[0]}_{image_id}.txt")

        # Check if the file has already been processed
        if bbox_file_path not in processed_files:
            # Write the image dimensions only once when the file is created
            with open(bbox_file_path, 'w') as bbox_file:
                bbox_file.write(f"[{image_height},{image_width}]\n")
            # Mark the file as processed
            processed_files.add(bbox_file_path)
        
        # Append the bounding box details to the file
        with open(bbox_file_path, 'a') as bbox_file:
            bbox_file.write(f"[{category_dict.get(category_id, 'unknown')}, {bbox}, {annotation['id']}, {image_id}]\n")
    
    # After extraction, classify the files
    classify_txt_files_by_prefix(base_folder)  # Change to the correct path if needed
    
    print("Bounding box details have been saved and classified.")

def classify_txt_files_by_prefix(input_folder):
    # Define the folder mapping based on the first two letters of the filename
    folder_mapping = {
        '01': 'textbooks',
        '02': 'newspapers',
        '03': 'magazines',
        '04': 'question_papers',
        '05': 'scientific_articles',
        '06': 'handwritten_notes'
    }

    # Loop through each file in the input folder
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            # Check if the file is a .txt file
            if filename.endswith(".txt"):
                # Get the first two letters of the filename
                prefix = filename[:2]
                
                # Get the destination folder name based on the prefix
                dest_folder_name = folder_mapping.get(prefix, 'others')

                # Create the destination folder path
                dest_folder = os.path.join(root, dest_folder_name)
                
                # If the destination folder doesn't exist, create it
                if not os.path.exists(dest_folder):
                    os.makedirs(dest_folder)
                
                # Define the source and destination file paths
                src_file = os.path.join(root, filename)
                dest_file = os.path.join(dest_folder, filename)
                
                # Move the file to the destination folder
                shutil.move(src_file, dest_file)
    
    print(f"Files have been classified into subfolders based on their prefixes.")

# Example usage

create_folders_and_save_bbox(json_file_path, input_folder)

def parse_bbox_line(line):
    line = line.strip()
    # Updated regex pattern to capture an additional number at the end
    pattern = re.compile(r'\[\s*([^\[\],]+?)\s*,\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\s*,\s*(\d+)\s*,\s*(\d+)\s*\]')
    match = pattern.match(line)

    if not match:
        raise ValueError(f"Line does not match expected format: {line}")

    label = match.group(1).strip()
    x1 = int(match.group(2))
    y1 = int(match.group(3))
    width = int(match.group(4))
    height = int(match.group(5))
    annotation_id = int(match.group(6))
    extra_number = int(match.group(7))  # Added to capture the additional number (880 in your case)

    return (label, x1, y1, width, height, annotation_id, extra_number)

def parse_image_size(line):
    line = line.strip().strip('[]')
    parts = line.split(',')

    if len(parts) != 2:
        raise ValueError(f"Image size line does not match expected format: {line}")

    width = int(parts[0].strip())
    height = int(parts[1].strip())

    return height, width

def is_overlapping(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    return not (x2_1 <= x1_2 or x1_1 >= x2_2 or y2_1 <= y1_2 or y1_1 >= y2_2)

def compute_intersection(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1[1], box1[2], box1[1] + box1[3], box1[2] + box1[4]
    x1_2, y1_2, x2_2, y2_2 = box2[1], box2[2], box2[1] + box2[3], box2[2] + box2[4]

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    if xi1 < xi2 and yi1 < yi2:
        return (xi1, yi1, xi2 - xi1, yi2 - yi1)
    else:
        return None

def split_box(big_box, small_box, label_suffix):
    x1_big, y1_big, x2_big, y2_big = big_box[1], big_box[2], big_box[1] + big_box[3], big_box[2] + big_box[4]
    x1_small, y1_small, x2_small, y2_small = small_box[1], small_box[2], small_box[1] + small_box[3], small_box[2] + small_box[4]

    new_boxes = []
    new_label = f"{big_box[0]}{label_suffix}"
    new_annotation_id = big_box[5]  # Reuse the annotation ID from the larger box
    extra_number = big_box[6]  # Preserve the extra number

    intersection = compute_intersection(big_box, small_box)
    if intersection:
        ix1, iy1, iwidth, iheight = intersection

        if iy1 > y1_big:
            new_boxes.append((new_label, x1_big, y1_big, big_box[3], iy1 - y1_big, new_annotation_id, extra_number))
        
        if y2_big > iy1 + iheight:
            new_boxes.append((new_label, x1_big, iy1 + iheight, big_box[3], y2_big - (iy1 + iheight), new_annotation_id, extra_number))
        
        if ix1 > x1_big:
            new_boxes.append((new_label, x1_big, max(y1_big, iy1), ix1 - x1_big, iheight, new_annotation_id, extra_number))
        
        if x2_big > ix1 + iwidth:
            new_boxes.append((new_label, ix1 + iwidth, max(y1_big, iy1), x2_big - (ix1 + iwidth), iheight, new_annotation_id, extra_number))

    return new_boxes

def handle_one_overlap_pair(bbox_details):
    processed_boxes = set()
    for i, box1 in enumerate(bbox_details):
        for j, box2 in enumerate(bbox_details):
            if i >= j:
                continue
            if is_overlapping(box1, box2):
                if box1 in processed_boxes or box2 in processed_boxes:
                    continue
                
                # Determine the label suffix based on overlap type
                if (box1[0] == 'formula' and box2[0] == 'paragraph') or (box1[0] == 'paragraph' and box2[0] == 'formula'):
                    label_suffix = '_1'
                else:
                    label_suffix = '_1'
                
                print(f"Processing overlap between: {box1} and {box2}")
                
                smaller_box, larger_box = (box1, box2) if (box1[3] * box1[4]) <= (box2[3] * box2[4]) else (box2, box1)
                
                new_boxes = split_box(larger_box, smaller_box, label_suffix)
                
                bbox_details = [box for box in bbox_details if box not in (box1, box2)]
                bbox_details.extend(new_boxes)
                
                processed_boxes.add(smaller_box)
                return bbox_details, smaller_box

    return bbox_details, None

def process_bboxes(file_path):
    bbox_details = []
    smaller_boxes = set()
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        image_size_line = lines[0]
        image_height, image_width = parse_image_size(image_size_line)
        
        for line in lines[1:]:
            try:
                bbox_details.append(parse_bbox_line(line))
            except ValueError as e:
                print(e)

        while True:
            bbox_details, smaller_box = handle_one_overlap_pair(bbox_details)
            if smaller_box is None:
                break
            print("Updated BBox Details:")
            for box in bbox_details:
                print(f"Box: {box}")
            print()
            smaller_boxes.add(smaller_box)

        with open(file_path, 'w') as file:
            file.write(f"[{image_width}, {image_height}]\n")
            for detail in bbox_details:
                file.write(f"[{detail[0]}, [{detail[1]}, {detail[2]}, {detail[3]}, {detail[4]}], {detail[5]}, {detail[6]}]\n")
            for box in smaller_boxes:
                file.write(f"[{box[0]}, [{box[1]}, {box[2]}, {box[3]}, {box[4]}], {box[5]}, {box[6]}]\n")

    except Exception as e:
        print(f"An error occurred: {e}")

def process_all_bboxes(base_folder):
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                process_bboxes(file_path)

# Example usage

process_all_bboxes(base_folder)
def parse_bbox_line(line):
    """Parse a bounding box line in the format [label, [x1, y1, width, height], annotation_id, image_id]."""
    try:
        # Updated regex pattern to include image_id
        pattern = r"\[(.*?)\s*,\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\],\s*(\d+),\s*(\d+)\]"
        match = re.match(pattern, line.strip())

        if not match:
            raise ValueError("Line doesn't match the expected format.")

        label = match.group(1).strip()  # Extract label
        coords = [int(match.group(i)) for i in range(2, 6)]  # Extract [x1, y1, width, height]
        annotation_id = int(match.group(6))  # Extract annotation ID
        image_id = int(match.group(7))  # Extract image ID

        return label, coords, annotation_id, image_id
    except Exception as e:
        # If any parsing fails, return None
        print(f"Failed to parse line: {line.strip()}. Error: {e}")
        return None

def filter_small_bboxes(input_file, min_height_pts=15):
    """Modify the same input .txt file by filtering out bounding boxes with height less than min_height_pts."""
    with open(input_file, 'r') as infile:
        lines = infile.readlines()

    image_dims = lines[0].strip()  # First line is image dimensions
    filtered_bboxes = [image_dims]

    # Process the bounding boxes
    for line in lines[1:]:
        # Skip any empty or invalid lines
        if not line.strip() or '[' not in line:
            continue

        # Manually parse the bounding box line
        parsed_bbox = parse_bbox_line(line)
        if parsed_bbox is None:
            print(f"Skipping invalid line: {line.strip()}")
            continue

        label, bbox_coords, annotation_id, image_id = parsed_bbox

        # Only keep bounding boxes where height is greater than or equal to min_height_pts
        if bbox_coords[3] >= min_height_pts:
            filtered_bboxes.append(line.strip())  # Keep this bounding box

    # Overwrite the input file with filtered bounding boxes
    with open(input_file, 'w') as outfile:
        for bbox in filtered_bboxes:
            outfile.write(f"{bbox}\n")

def process_all_txt_files_in_folder(base_folder_2, min_height_pts=15):
    """
    Traverse all subfolders and process all .txt files found inside,
    applying the filter_small_bboxes function to each one.
    This will modify the .txt files in place.
    """
    for root, dirs, files in os.walk(base_folder_2):
        for file in files:
            if file.endswith('.txt'):
                # Full path to the input .txt file
                input_file = os.path.join(root, file)

                # Process the .txt file and update it in place
                print(f"Processing {input_file}")
                filter_small_bboxes(input_file, min_height_pts)

# Specify the base folder to process


# Process all .txt files in the base folder and subfolders
process_all_txt_files_in_folder(base_folder_2)
def remove_suffixes(label):
    """Remove any trailing _1, _1_1, _1_1_1 from the label."""
    return re.sub(r'(_1)+$', '', label)  # This regex will match any number of _1's at the end of the label

def process_bboxes(input_file):
    """Process bounding boxes by cleaning up the labels and updating the file in place."""
    with open(input_file, 'r') as infile:
        lines = infile.readlines()

    if not lines:
        print(f"File {input_file} is empty.")
        return

    image_dims = lines[0].strip()  # First line is image dimensions
    processed_bboxes = [image_dims]

    # Updated regex to match label, bbox coordinates, and optionally the extra annotation ID
    bbox_pattern = re.compile(r'\[\s*([^,]+?)\s*,\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\s*,\s*(\d+)(?:,\s*(\d+))?\s*\]')

    for line in lines[1:]:
        line = line.strip()

        # Skip empty or invalid lines
        if not line or '[' not in line:
            print(f"Skipping invalid or empty line: {line}")
            continue

        # Match the line against the regex
        match = bbox_pattern.match(line)

        if not match:
            print(f"Failed to match line: {line}")
            continue

        try:
            # Extract label and bbox details
            label = match.group(1).replace("'", "").strip()  # Remove quotes from the label
            x1, y1, width, height = map(int, [match.group(2), match.group(3), match.group(4), match.group(5)])
            annotation_id = int(match.group(6))
            extra_annotation_id = match.group(7)  # Optional extra annotation ID
            
            # Remove suffixes like _1 from the label
            cleaned_label = remove_suffixes(label)

            # Reconstruct the line with the cleaned label and annotation IDs (if any)
            if extra_annotation_id:
                new_line = f"[{cleaned_label}, [{x1}, {y1}, {width}, {height}], {annotation_id}, {extra_annotation_id}]"
            else:
                new_line = f"[{cleaned_label}, [{x1}, {y1}, {width}, {height}], {annotation_id}]"

            # Add the processed line to the list
            processed_bboxes.append(new_line)

        except Exception as e:
            print(f"Error processing line: {line}. Error: {e}")
            continue

    # Ensure that at least one bounding box was processed
    if len(processed_bboxes) > 1:
        # Overwrite the input file with processed bounding boxes
        with open(input_file, 'w') as outfile:
            for bbox in processed_bboxes:
                outfile.write(f"{bbox}\n")
    else:
        print(f"No valid bounding boxes found for {input_file}, leaving the file unchanged.")

def process_all_txt_files_in_folder(base_folder_3):
    """
    Traverse all subfolders and process all .txt files found inside,
    applying the process_bboxes function to each one.
    This will modify the .txt files in place.
    """
    for root, dirs, files in os.walk(base_folder_3):
        for file in files:
            if file.endswith('.txt'):
                # Full path to the input .txt file
                input_file = os.path.join(root, file)

                # Process the .txt file and update it in place
                print(f"Processing {input_file}")
                process_bboxes(input_file)

process_all_txt_files_in_folder(base_folder_3)



