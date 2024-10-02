import os

def divide_table_bbox(x1, y1, width, height, label, annotation_id):
    """
    Divide a table bounding box into cells of 28 pts height and 3 equal columns.
    """
    num_rows = height // 28
    num_cols = 3
    cell_width = width // num_cols
    new_bboxes = []

    for row in range(num_rows):
        for col in range(num_cols):
            cell_x1 = x1 + col * cell_width
            cell_y1 = y1 + row * 28
            new_label = f'{label}_row{row+1}_col{col+1}'
            new_bboxes.append([cell_x1, cell_y1, cell_width, 28, new_label, annotation_id])
    return new_bboxes

def parse_bbox_line(line):
    """
    Parse a line of bounding box data from the input file.
    """
    try:
        # Split the line into its components
        line = line.strip()
        
        # Find the last comma that precedes the annotation ID
        last_comma_index = line.rfind(',')
        
        # Extract the annotation ID and convert to an integer
        annotation_id = int(line[last_comma_index + 1:].strip(" ]"))

        # Extract the rest of the line (label and bbox)
        label_bbox_part = line[:last_comma_index].strip("[] ")
        
        # Separate label and bbox parts
        label, bbox_str = label_bbox_part.split(", [", 1)
        label = label.strip().strip("'")
        bbox = list(map(int, bbox_str.strip("[] ").split(',')))

        return label, bbox, annotation_id
    except Exception as e:
        raise ValueError(f"Line format is incorrect: {line}, Error: {e}")

def process_bboxes(file_path):
    """
    Process the bboxes from the input file and rewrite the results back to the same file.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract image dimensions
    image_dimensions = lines[0].strip()

    # Initialize the new bounding boxes list
    new_bboxes = []

    # Process each bounding box
    for line in lines[1:]:
        try:
            label, bbox, annotation_id = parse_bbox_line(line)
            x1, y1, width, height = bbox

            if label == 'table':
                # Keep the original table dimensions
                new_bboxes.append([x1, y1, width, height, label, annotation_id])
                # Divide the table into cells and add to the new bounding boxes list
                new_bboxes.extend(divide_table_bbox(x1, y1, width, height, label, annotation_id))
            else:
                new_bboxes.append([x1, y1, width, height, label, annotation_id])
        except ValueError as e:
            print(f"Skipping line due to error: {e}")

    # Rewrite the new bounding boxes back to the same input file
    with open(file_path, 'w') as file:
        file.write(f'{image_dimensions}\n')
        for bbox in new_bboxes:
            file.write(f'[ {bbox[4]}, [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}], {bbox[5]}]\n')

    print(f"Bounding boxes processed and saved back to {file_path}")

def process_directory(parent_directory):
    """
    Traverse the parent directory and process all bbox files in the subfolders.
    """
    for root, _, files in os.walk(parent_directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                process_bboxes(file_path)

if __name__ == "__main__":
    parent_directory = r'M6Doc/BBOX_val'
    process_directory(parent_directory)
