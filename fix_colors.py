import os
import re

def find_and_replace_in_file(file_path):
    """
    Find instances of ft.Colors and replace with ft.Colors in a file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace ft.Colors with ft.Colors
        modified_content = re.sub(r'ft\.Colors\.', 'ft.Colors.', content)
        
        # If changes were made, write the modified content back to the file
        if content != modified_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(modified_content)
            print(f"Updated file: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def process_directory(directory):
    """
    Process all Python files in the given directory and its subdirectories
    """
    files_updated = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if find_and_replace_in_file(file_path):
                    files_updated += 1
    
    return files_updated

if __name__ == "__main__":
    # Base directory to start from
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Process Python files in the src directory
    src_dir = os.path.join(base_dir, 'src')
    
    print(f"Starting to process files in {src_dir}")
    files_updated = process_directory(src_dir)
    
    print(f"Finished processing. {files_updated} files were updated.")
