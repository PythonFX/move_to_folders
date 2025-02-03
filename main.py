import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from drag_drop_frame import DragDropFrame
import file_utils




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JAV 封面视频整理小工具")

        # Drag and Drop Area for Sorting Files
        self.move_folder_frame = DragDropFrame(400, 120, 'red')
        self.move_folder_frame.setHandler(self.on_drop_for_put_into_folders)
        self.sort_drop_label = QLabel("拖拽多个视频和封面图\n会把每个视频整理成独立文件夹", self.move_folder_frame)
        self.sort_drop_layout = QVBoxLayout(self.move_folder_frame)
        self.sort_drop_layout.addWidget(self.sort_drop_label)

        # Drag and Drop Area for Moving Files to Parent
        self.flatten_folder_frame = DragDropFrame(400, 120, 'green')
        self.flatten_folder_frame.setHandler(self.on_drop_for_remove_folders)
        self.move_drop_label = QLabel("拖拽一个或多个文件\n会把同级全部视频文件夹内容平铺开", self.flatten_folder_frame)
        self.move_drop_layout = QVBoxLayout(self.flatten_folder_frame)
        self.move_drop_layout.addWidget(self.move_drop_label)

        # Folder Path Input
        self.folder_path_entry = QLineEdit(self)

        # Button to process files in folder
        self.process_button = QPushButton("整理到各个文件夹", self)
        self.process_button.clicked.connect(self.on_move_to_folders_btn_click)

        # Button to process files in folder
        self.remove_folder_button = QPushButton("视频和封面图平铺开", self)
        self.remove_folder_button.clicked.connect(self.on_remove_folder_btn_click)

        # Button to process files in folder
        self.print_folder_contents_button = QPushButton("输出该文件夹下的全部内容", self)
        self.print_folder_contents_button.clicked.connect(self.on_print_folder_contents)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.move_folder_frame)
        layout.addWidget(self.flatten_folder_frame)
        layout.addWidget(self.folder_path_entry)
        layout.addWidget(self.process_button)
        layout.addWidget(self.remove_folder_button)
        layout.addWidget(self.print_folder_contents_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def dragEnterEvent(self, event):
        print('dragEnterEvent')
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # urls = event.mimeData().urls()
        # if not urls:
        #     return
        # filePaths = [url.toLocalFile() for url in urls]
        # self.processFiles(filePaths)
        if self.move_folder_frame.underMouse():
            self.on_drop_for_put_into_folders(event)
        elif self.flatten_folder_frame.underMouse():
            self.on_drop_for_remove_folders(event)

    def on_drop_for_put_into_folders(self, event):
        file_paths = event.mimeData().urls()
        file_paths = [path.toLocalFile() for path in file_paths]
        self.sort_and_organize_files(file_paths)

    def on_drop_for_remove_folders(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        file_path = file_utils.clean_path(file_path)
        self.move_files_to_parent_and_remove_subfolders(file_path)

    def on_move_to_folders_btn_click(self):
        folder_path = self.folder_path_entry.text()
        if os.path.isdir(folder_path):
            file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                          os.path.isfile(os.path.join(folder_path, f))]
            self.sort_and_organize_files(file_paths)
        else:
            print("Invalid folder path")

    def on_remove_folder_btn_click(self):
        folder_path = self.folder_path_entry.text()
        self.move_files_to_parent(folder_path)

    def on_print_folder_contents(self):
        folder_path = self.folder_path_entry.text()
        all_paths = []
        for path in os.listdir(folder_path):
            if path.startswith('.'):
                continue
            all_paths.append(path)
        all_paths.sort()
        for path in all_paths:
            print(path)

    def sort_and_organize_files(self, file_paths):
        # ignore folder path
        file_paths = [path for path in file_paths if not os.path.isdir(path)]

        # Define the file extensions for videos and images
        video_extensions = ['mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm']
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

        # Separate the file paths into videos and images
        video_files = [file for file in file_paths if file_utils.extension(file).lower() in video_extensions]
        image_files = [file for file in file_paths if file_utils.extension(file).lower() in image_extensions]

        # Function to create a directory if it doesn't exist
        def create_dir_if_not_exists(dir_name):
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

        # Function to move a file using os.rename
        def move_file(file_path, target_dir):
            target_path = os.path.join(target_dir, file_utils.full_filename(file_path))
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

        def get_video_prefix(video):
            filename = file_utils.filename(video).lower()
            # remove leading bracket and everything in it
            if filename.startswith('['):
                closing_bracket_index = filename.find(']')
                if closing_bracket_index != -1:
                    filename = filename[closing_bracket_index + 1:]
                    print(f'cleaned filename = {filename}')
            if filename.startswith('【'):
                closing_bracket_index = filename.find('】')
                if closing_bracket_index != -1:
                    filename = filename[closing_bracket_index + 1:]
                    print(f'cleaned filename = {filename}')
            common_patterns = ['hhd800.com@', '[thz.la]', '4k2.com@']
            # removing common
            for pattern in common_patterns:
                if pattern in filename:
                    filename = filename.replace(pattern, '')
            return filename[:prefix_len]

        # Iterate over each image file
        for image in image_files:
            image_name = file_utils.full_filename(image)
            first_space_idx = image_name.find(' ')
            if first_space_idx == -1:
                prefix_len = 8  # like ABP-986
            else:
                prefix_len = first_space_idx
            image_prefix = image_name.split('.')[0][:prefix_len].lower()
            print(f'image_prefix = {image_prefix}')
            found_video = False

            # Iterate over each video file to find a match
            for video in video_files:
                video_prefix = get_video_prefix(video)
                print(f'video_prefix = {video_prefix}')
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

    def move_files_to_parent_and_remove_subfolders(self, path):
        # Check if the path is valid
        if not os.path.exists(path):
            print(f"The path {path} does not exist.")
            return

        # Get the parent directory of the provided path
        parent_path = file_utils.parent(path)
        self.move_files_to_parent(parent_path)

    def move_files_to_parent(self, parent_path):
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())