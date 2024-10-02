import os
import re

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
base_folder = r'M6Doc\BBOX_val'
process_all_bboxes(base_folder)
