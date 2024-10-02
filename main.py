import subprocess
import os

# Base directory where your Python scripts are located
base_dir = "C:\\Users\\shreya reddy\\Desktop\\synt\\M6Doc"

# List of Python scripts to run in order
scripts = [
    "normal__fill.py",
    "extract_text_bbox.py",
    "clear_textlines.py",
    "textline_fill.py"  # Updated to include the correct name
]

def run_script(script_name):
    script_path = os.path.join(base_dir, script_name)
    
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        return False  # Return False if script is not found
    
    try:
        # Run the Python script and wait for it to complete
        subprocess.run(["python", script_path], check=True)
        print(f"Successfully executed {script_name}")
        return True  # Return True if the script executed successfully

    except subprocess.CalledProcessError as e:
        print(f"Error while executing {script_name}: {e}")
        return False  # Return False if there was an error

if __name__ == "__main__":
    for script in scripts:
        success = run_script(script)  # Run each script
        if not success:
            print(f"Stopping further execution due to error in {script}.")
            break  # Stop execution if any script fails
