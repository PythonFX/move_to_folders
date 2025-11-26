import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt
from drag_drop_frame import DragDropFrame
import file_utils
from service.actors_service import ActorsService
from service.move_video_service import MoveVideoService





class MoveVideoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_path = '/Users/vincent/Downloads/bus_new_download'
        self.target_path = '/Volumes/XSK'
        self.setWindowTitle("JAV 封面视频整理小工具")
        self.service = MoveVideoService(ActorsService().actors, self.target_path)

        # Rename Video File Names
        self.move_video_frame = DragDropFrame(400, 100, 'purple')
        self.move_video_frame.setHandler(self.on_drop_for_move_video_files)
        self.move_video_label = QLabel("自动分析选中文件中的视频文件，移动到已有actor文件夹；\n或引导创建actor文件夹", self.move_video_frame)
        self.move_video_layout = QVBoxLayout(self.move_video_frame)
        self.move_video_layout.addWidget(self.move_video_label)

        # Folder Path Input
        self.folder_path_entry = QLineEdit(self)
        self.folder_path_entry.setText(self.default_path)

        self.current_actor_label = QLabel(self)
        self.current_actor_label.setText("当前处理的演员：")
        self.current_actor_entry = QLineEdit(self)
        self.current_actor_entry.textChanged.connect(self.on_actor_name_changed)

        self.current_video_label = QLabel(self)
        self.current_video_label.setText("当前处理的片名：")
        self.current_video_label.setWordWrap(True)
        self.current_video_label.setFixedWidth(400)
        self.current_video_label.setTextInteractionFlags(Qt.TextSelectableByMouse)


        # Add buttons
        self.move_video_button = QPushButton("移动视频文件", self)
        self.move_video_button.clicked.connect(self.on_move_video_files)

        self.confirm_frame = QFrame()
        # self.confirm_frame.setFixedSize(400, 60)
        # self.create_button = QPushButton("创建文件夹", self.confirm_frame)
        # self.create_button.setStyleSheet("""
        #             QPushButton {
        #                 /* This preserves the native styling */
        #                 border: none;
        #                 background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
        #                                               stop:0 rgba(0, 0, 255, 160),
        #                                               stop:1 rgba(0, 0, 200, 160));
        #                 color: white;
        #                 border-radius: 5px;
        #                 padding: 3px;
        #             }
        #             QPushButton:hover {
        #                 background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
        #                                               stop:0 rgba(50, 50, 255, 160),
        #                                               stop:1 rgba(0, 0, 220, 160));
        #             }
        #         """)
        # self.create_button.clicked.connect(self.on_create_actor_folder)
        self.confirm_button = QPushButton("创建文件夹并移动", self.confirm_frame)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                /* This preserves the native styling */
                border: none;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(0, 255, 0, 100),
                                              stop:1 rgba(0, 200, 0, 100));
                color: white;
                border-radius: 5px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(50, 255, 50, 100),
                                              stop:1 rgba(0, 255, 0, 100));
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_move_video_file)
        self.cancel_button = QPushButton("取消移动", self.confirm_frame)
        self.cancel_button.clicked.connect(self.on_cancel_move_video_file)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                /* This preserves the native styling */
                border: none;
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(255, 0, 0, 100),
                                              stop:1 rgba(200, 0, 0, 100));
                color: white;
                border-radius: 5px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(255, 50, 50, 100),
                                              stop:1 rgba(220, 0, 0, 100));
            }
        """)
        self.confirm_layout = QHBoxLayout(self.confirm_frame)
        self.confirm_layout.addWidget(self.confirm_button)
        self.confirm_layout.addWidget(self.cancel_button)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.move_video_frame)
        layout.addWidget(self.folder_path_entry)
        layout.addWidget(self.move_video_button)
        layout.addWidget(self.current_actor_label)
        layout.addWidget(self.current_actor_entry)
        layout.addWidget(self.current_video_label)
        layout.addWidget(self.confirm_frame)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def on_drop_for_move_video_files(self, event):
        return
        file_paths = event.mimeData().numbers()
        dir_paths = [path.toLocalFile() for path in file_paths]
        self.service.process_files(dir_paths)
        self.current_video_label.setText(f"当前处理的片名：{self.service.video_name}")
        self.current_actor_entry.setText(self.service.actor_name)


    def on_move_video_files(self):
        folder_path = self.folder_path_entry.text()
        if os.path.isdir(folder_path):
            dir_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                         os.path.isdir(os.path.join(folder_path, f))]
            self.service.process_files(dir_paths)
            self.current_video_label.setText(f"当前处理的片名：{self.service.video_name}")
            if self.service.actor_name:
                # self.current_actor_label.setText(f"当前处理的演员：{self.service.actor_name}")
                self.current_actor_entry.setText(self.service.actor_name)
            if self.service.need_to_create_actor_folder:
                self.confirm_button.setText('创建文件夹并移动')
            else:
                self.confirm_button.setText('移动文件')
        else:
            print("Invalid folder path")

    def on_create_actor_folder(self):
        self.service.create_actor_folder()

    def on_confirm_move_video_file(self):
        if self.service.actor_name:
            self.confirm_button.setText('移动文件ing...')
        self.service.create_actor_folder()
        self.service.move_video()
        self._reset_labels()

    def on_cancel_move_video_file(self):
        self.service.add_ignore_video()
        self._reset_labels()

    def on_actor_name_changed(self):
        actor_name = self.current_actor_entry.text()
        if not len(actor_name):
            return
        self.service.actor_name = actor_name



    def _reset_labels(self):
        self.current_video_label.setText("当前处理的片名：")
        self.current_actor_entry.setText('')












if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MoveVideoWindow()
    window.show()
    sys.exit(app.exec_())