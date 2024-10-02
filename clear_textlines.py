import os
import json
import glob

def clear_text_and_textlines_in_json_folder(json_folder_path):
    # Find all JSON files in the specified folder
    json_files = glob.glob(os.path.join(json_folder_path, '*.json'))

    if not json_files:
        print(f"No JSON files found in the folder: {json_folder_path}")
        return

    # Process each JSON file in the folder
    for json_file_path in json_files:
        print(f"Processing file: {json_file_path}")
        # Open the JSON file to read its contents
        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            continue

        # Check if 'annotations' is present in the JSON
        if "annotations" in data:
            # Iterate through all annotations and clear 'text' and 'textlines'
            for annotation in data["annotations"]:
                annotation["text"] = ""  # Clear the text
                annotation["textlines"] = []  # Clear textlines
                print(f"Cleared text and textlines for annotation ID: {annotation['id']}")

        # Write the updated JSON back to the file
        try:
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
            print(f"Successfully cleared text and textlines and updated the file: {json_file_path}")
        except Exception as e:
            print(f"Error writing JSON file: {e}")

# Example usage
json_folder_path = 'output_jsons'  # Change this to your folder path
clear_text_and_textlines_in_json_folder(json_folder_path)
