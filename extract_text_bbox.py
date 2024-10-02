import os
import json

# Function to extract bounding boxes and image_id from JSON
def get_bboxes_from_json(json_file, json_filename_as_id):
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    bboxes = []
    
    # Extract the image_id from the first annotation or fallback to the filename
    image_id = json_data["annotations"][0].get("image_id", None) if json_data["annotations"] else None

    # Use the json filename (without extension) as image_id if not found in JSON
    if image_id is None:
        image_id = json_filename_as_id

    for annotation in json_data["annotations"]:
        category_id = annotation["label"]
        bbox_id = annotation["id"]

        # Main bounding box for the text
        main_bbox = [
            annotation["bbox"]["x1"],
            annotation["bbox"]["y1"],
            annotation["bbox"]["width"],
            annotation["bbox"]["height"]
        ]
        
        # Append the category_id, main bbox, bbox_id, and the image_id as a new entry
        bboxes.append([category_id, main_bbox, bbox_id, image_id])
        
        # Textline bounding boxes
        for line in annotation.get("textlines", []):
            line_bbox = line["bbox"]
            # Append each textline bounding box with the category_id, bbox_id, and image_id
            bboxes.append([category_id, line_bbox, bbox_id, image_id])
    
    return image_id, bboxes

# Function to rewrite bounding boxes in the txt file, skipping the first row
def rewrite_bboxes_in_txt(txt_file, new_bboxes):
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Keep the first line and discard the rest
    first_line = lines[0] if lines else ""

    # Prepare the new bbox content to write
    bboxes_content = ""
    for bbox in new_bboxes:
        bboxes_content += f'[{bbox[0]}, [{bbox[1][0]}, {bbox[1][1]}, {bbox[1][2]}, {bbox[1][3]}], {bbox[2]}, {bbox[3]}]\n'

    # Rewrite the file: keep the first line, then overwrite the rest with new bboxes
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(first_line)  # Write the first line back
        f.write(bboxes_content)  # Write the new bounding boxes

# Main function to handle folders and files
def process_folders(json_folder, txt_folder):
    # Loop through JSON files in the json_folder
    for json_filename in os.listdir(json_folder):
        if json_filename.endswith(".json"):
            json_file_path = os.path.join(json_folder, json_filename)
            
            # Use the JSON file name (without extension) as a fallback image_id
            json_filename_as_id = os.path.splitext(json_filename)[0]

            # Extract image_id and bounding boxes from the corresponding JSON file
            image_id, extracted_bboxes = get_bboxes_from_json(json_file_path, json_filename_as_id)

            if image_id is None:
                print(f"Warning: No image_id found in {json_filename}")
                continue  # Skip if no image_id is found
            
            # Search for the txt file in txt_folder subfolders that ends with the same image_id
            for subfolder in os.listdir(txt_folder):
                subfolder_path = os.path.join(txt_folder, subfolder)
                if os.path.isdir(subfolder_path):  # Ensure it's a folder
                    for txt_filename in os.listdir(subfolder_path):
                        if txt_filename.endswith(f"{image_id}.txt"):
                            txt_file_path = os.path.join(subfolder_path, txt_filename)
                            
                            # Rewrite the txt file with the extracted bboxes, skipping the first row
                            rewrite_bboxes_in_txt(txt_file_path, extracted_bboxes)
                            print(f"Updated: {txt_file_path}")

# Example usage:
if __name__ == "__main__":
    # Replace these with your actual folder paths
    json_folder = r'output_jsons'
    txt_folder = r'M6Doc\BBOX_val'
    process_folders(json_folder, txt_folder)
