import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD


def on_drop_for_put_into_folders(event):
    file_paths = root.tk.splitlist(event.data)
    sort_and_organize_files(file_paths)

def on_drop_for_remove_folders(event):
    file_path = root.tk.splitlist(event.data)[0]  # Take the first dropped file
    move_files_to_parent_and_remove_subfolders(file_path)

def on_move_to_folders_btn_click():
    folder_path = folder_path_entry.get()
    if os.path.isdir(folder_path):
        file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        sort_and_organize_files(file_paths)
    else:
        print("Invalid folder path")

def on_remove_folder_btn_click():
    folder_path = folder_path_entry.get()
    move_files_to_parent(folder_path)

def on_print_folder_contents():
    folder_path = folder_path_entry.get()
    all_paths = []
    for path in os.listdir(folder_path):
        if path.startswith('.'):
            continue
        all_paths.append(path)
    all_paths.sort()
    for path in all_paths:
        print(path)

def sort_and_organize_files(file_paths):
    # ignore folder path
    file_paths = [path for path in file_paths if not os.path.isdir(path)]

    # Define the file extensions for videos and images
    video_extensions = ['mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm']
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

    # Separate the file paths into videos and images
    video_files = [file for file in file_paths if file.split('.')[-1].lower() in video_extensions]
    image_files = [file for file in file_paths if file.split('.')[-1].lower() in image_extensions]

    # Function to create a directory if it doesn't exist
    def create_dir_if_not_exists(dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    # Function to move a file using os.rename
    def move_file(file_path, target_dir):
        target_path = os.path.join(target_dir, os.path.basename(file_path))
        os.rename(file_path, target_path)

    def get_folder_name(s, is_4k):
        last_dot_index = s.rfind('.')
        if last_dot_index != -1:
            folder_name = s[:last_dot_index]
        else:
            folder_name = s
        if is_4k:
            first_space_index = folder_name.find(' ')
            if first_space_index != -1:
                # insert '[4K]' at position first_space_index
                folder_name = folder_name[:first_space_index] + '[4K]' + folder_name[first_space_index:]
        return folder_name


    # Iterate over each image file
    for image in image_files:
        image_basename = os.path.basename(image)
        first_space_idx = image_basename.find(' ')
        if first_space_idx == -1:
            prefix_len = 8  # like ABP-986
        else:
            prefix_len = first_space_idx
        image_prefix = image_basename.split('.')[0][:prefix_len].lower()
        found_video = False

        # Iterate over each video file to find a match
        for video in video_files:
            video_prefix = os.path.basename(video).split('.')[0][:prefix_len].lower()
            if image_prefix == video_prefix:
                folder_name = get_folder_name(os.path.basename(image), '4k' in video)
                parent_folder_path = os.path.dirname(image)
                folder_path = os.path.join(parent_folder_path, folder_name)
                create_dir_if_not_exists(folder_path)
                move_file(image, folder_path)
                move_file(video, folder_path)
                video_files.remove(video)
                found_video = True
                break

        if not found_video:
            print(f'No video found for {os.path.basename(image)}')

def move_files_to_parent_and_remove_subfolders(path):
    # Check if the path is valid
    if not os.path.exists(path):
        print(f"The path {path} does not exist.")
        return

    # Get the parent directory of the provided path
    parent_path = os.path.dirname(path)
    move_files_to_parent(parent_path)

def move_files_to_parent(parent_path):
    # Iterate over each item in the parent directory
    for item in os.listdir(parent_path):
        sub_path = os.path.join(parent_path, item)

        # Check if the item is a directory
        if os.path.isdir(sub_path):
            has_file = False
            # Move each file in this subdirectory to the parent directory
            for file in os.listdir(sub_path):
                file_path = os.path.join(sub_path, file)
                # Ensure it's a file and not a directory
                if os.path.isfile(file_path):
                    # Generate new path in the parent directory
                    new_path = os.path.join(parent_path, file)
                    has_file = True
                    # Rename (move) the file
                    os.rename(file_path, new_path)

            if has_file:
                os.rmdir(sub_path)


# Create the main window
root = TkinterDnD.Tk()
root.title("JAV封面视频整理小工具")

# Drag and Drop Area for Sorting Files
sort_drop_frame = tk.Frame(root, width=400, height=100, bg="lightgrey")
sort_drop_frame.pack(pady=20)
sort_drop_frame.propagate(False)
sort_drop_frame.drop_target_register(DND_FILES)
sort_drop_frame.dnd_bind('<<Drop>>', on_drop_for_put_into_folders)

sort_drop_label = tk.Label(sort_drop_frame, text="选择多个视频和封面图拖拽到这里，整理成每个文件夹", bg="lightgrey")
sort_drop_label.pack(expand=True)

# Drag and Drop Area for Moving Files to Parent
move_drop_frame = tk.Frame(root, width=400, height=100, bg="lightgrey")
move_drop_frame.pack(pady=20)
move_drop_frame.propagate(False)
move_drop_frame.drop_target_register(DND_FILES)
move_drop_frame.dnd_bind('<<Drop>>', on_drop_for_remove_folders)

move_drop_label = tk.Label(move_drop_frame, text="拖拽一个或多个文件，会把该文件同级的\n所有文件夹内的视频和封面图平铺开，并移除这些文件夹", bg="lightgrey")
move_drop_label.pack(expand=True)

# Folder Path Input
folder_path_entry = tk.Entry(root, width=50)
folder_path_entry.pack(pady=10)

# Button to process files in folder
process_button = tk.Button(root, text="整理到各个文件夹", command=on_move_to_folders_btn_click)
process_button.pack()

# Button to process files in folder
remove_folder_button = tk.Button(root, text="视频和封面图平铺开", command=on_remove_folder_btn_click)
remove_folder_button.pack()

# Button to process files in folder
remove_folder_button = tk.Button(root, text="输出该文件夹下的全部内容", command=on_print_folder_contents)
remove_folder_button.pack()

# Run the application
root.mainloop()
