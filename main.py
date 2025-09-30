import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from drag_drop_frame import DragDropFrame
import file_utils
from service.organize_file_service import OrganizeFileService
from service.rename_service import RenameService
from service.actors_service import ActorsService




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_path = '/Users/vincent/Downloads/bus_new_download'
        self.setWindowTitle("JAV 封面视频整理小工具")

        # Services
        self.organize_file_service = OrganizeFileService()
        self.rename_service = RenameService()
        self.actors_service = ActorsService()

        # Rename Video File Names
        self.rename_video_frame = DragDropFrame(400, 100, 'purple')
        self.rename_video_frame.setHandler(self.on_drop_for_rename_video_files)
        self.rename_video_label = QLabel("将选中文件中的视频文件名，做清洁化", self.rename_video_frame)
        self.rename_video_layout = QVBoxLayout(self.rename_video_frame)
        self.rename_video_layout.addWidget(self.rename_video_label)

        # Drag and Drop Area for Sorting Files
        self.move_folder_frame = DragDropFrame(400, 100, 'red')
        self.move_folder_frame.setHandler(self.on_drop_for_put_into_folders)
        self.sort_drop_label = QLabel("选择多个视频和封面图拖拽到这里，整理成每个文件夹", self.move_folder_frame)
        self.sort_drop_layout = QVBoxLayout(self.move_folder_frame)
        self.sort_drop_layout.addWidget(self.sort_drop_label)

        # Drag and Drop Area for Moving Files to Parent
        self.flatten_folder_frame = DragDropFrame(400, 100, 'green')
        self.flatten_folder_frame.setHandler(self.on_drop_for_remove_folders)
        self.move_drop_label = QLabel("拖拽一个或多个文件，会把该文件同级的\n所有文件夹内的视频和封面图平铺开，并移除这些文件夹", self.flatten_folder_frame)
        self.move_drop_layout = QVBoxLayout(self.flatten_folder_frame)
        self.move_drop_layout.addWidget(self.move_drop_label)

        # Folder Path Input
        self.folder_path_entry = QLineEdit(self)
        self.folder_path_entry.setText(self.default_path)

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
        layout.addWidget(self.rename_video_frame)
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

    def on_drop_for_rename_video_files(self, event):
        file_paths = event.mimeData().urls()
        file_paths = [path.toLocalFile() for path in file_paths]
        self.rename_service.rename_files(file_paths)

    def on_drop_for_put_into_folders(self, event):
        file_paths = event.mimeData().urls()
        file_paths = [path.toLocalFile() for path in file_paths]
        self.organize_file_service.sort_and_organize_files(file_paths)

    def on_drop_for_remove_folders(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        file_path = file_utils.clean_path(file_path)
        self.move_files_to_parent_and_remove_subfolders(file_path)

    def on_move_to_folders_btn_click(self):
        folder_path = self.folder_path_entry.text()
        if os.path.isdir(folder_path):
            file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                          os.path.isfile(os.path.join(folder_path, f))]
            self.organize_file_service.sort_and_organize_files(file_paths)
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