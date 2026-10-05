import os
import shutil
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from drag_drop_frame import DragDropFrame
import file_utils
from service.organize_file_service import OrganizeFileService
from service.rename_service import RenameService
from service.actors_service import ActorsService


class CoverDownloadWorker(QThread):
    """后台跑 jav_metadata 封面下载流水线，避免冻结 GUI"""
    progress = pyqtSignal(str)
    done = pyqtSignal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        from jav_metadata.config import load_config
        from jav_metadata.logger import ResultLogger
        from jav_metadata.scanner import scan_movie_root
        from jav_metadata.scheduler import run, summarize

        config = load_config()
        file_logger = ResultLogger()
        worker = self

        class SignalLogger:
            """文件日志照写，同时把每个任务结果推到状态栏"""
            def log(self, task):
                file_logger.log(task)
                worker.progress.emit(f'{task.number or "-"} | {task.status}')

            def info(self, message):
                file_logger.info(message)

        try:
            tasks = scan_movie_root(self.folder_path, file_logger)
            tasks = run(tasks, config, SignalLogger())
            summarize(tasks, file_logger)
            counts = {}
            for t in tasks:
                counts[t.status] = counts.get(t.status, 0) + 1
            summary = ', '.join(f'{k}:{v}' for k, v in sorted(counts.items()))
            self.done.emit(f'封面下载完成 [{summary}] 日志: {file_logger.log_path}')
        except Exception as e:
            self.done.emit(f'封面下载出错: {e}')


class MagnetFetchWorker(QThread):
    """后台提取单个番号的磁力下载列表，避免冻结 GUI"""
    done = pyqtSignal(str, list, str)  # number, magnets, error

    def __init__(self, number):
        super().__init__()
        self.number = number

    def run(self):
        from jav_metadata.config import load_config
        from jav_metadata.search import get_movie_magnets
        try:
            magnets = get_movie_magnets(load_config(), self.number)
            self.done.emit(self.number, magnets, '')
        except Exception as e:
            self.done.emit(self.number, [], str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_path = '/Users/vincent/Downloads/bus_new_download'
        self.setWindowTitle("JAV 封面视频整理小工具")

        # Persisted settings (remembers last used folder path across sessions)
        self.settings = QSettings("JavManager", "MoveToFolders")

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
        # Restore last used path; fall back to default on first run
        self.folder_path_entry.setText(self.settings.value("last_folder_path", self.default_path))
        # Persist whenever the user finishes editing the field
        self.folder_path_entry.editingFinished.connect(self._save_folder_path)

        # Button to process files in folder
        self.process_button = QPushButton("整理到各个文件夹", self)
        self.process_button.clicked.connect(self.on_move_to_folders_btn_click)

        # Button to download covers for all videos under the configured path
        self.download_covers_button = QPushButton("下载全部视频的封面图", self)
        self.download_covers_button.clicked.connect(self.on_download_covers_btn_click)

        # Movie number input + button to fetch all magnet download info
        self.magnet_number_entry = QLineEdit(self)
        self.magnet_number_entry.setPlaceholderText("输入番号,例: IPZZ-937")
        self.fetch_magnets_button = QPushButton("提取该番号的下载信息", self)
        self.fetch_magnets_button.clicked.connect(self.on_fetch_magnets_btn_click)

        # Button to process files in folder
        self.remove_folder_button = QPushButton("视频和封面图平铺开", self)
        self.remove_folder_button.clicked.connect(self.on_remove_folder_btn_click)

        # Button to pull large videos (>100MB) out of subfolders into the root folder
        self.extract_large_videos_button = QPushButton("子文件夹大视频(>100MB)移到根目录", self)
        self.extract_large_videos_button.clicked.connect(self.on_extract_large_videos_btn_click)

        # Button to process files in folder
        self.print_folder_contents_button = QPushButton("输出该文件夹下的全部内容", self)
        self.print_folder_contents_button.clicked.connect(self.on_print_folder_contents)
        
        # Button to start move video folders in current workspace
        self.start_move_video_folders_button = QPushButton("开始移动视频文件夹们", self)
        self.start_move_video_folders_button.clicked.connect(self.on_start_move_videos_btn_click)
        
        self.current_process_video_label = QLabel("当前待移动的视频名称")
        self.current_process_video_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.current_video_actor_entry = QLineEdit(self)
        self.current_video_actor_entry.setText("当前演员名")
        self.confirm_move_button = QPushButton("确认移动视频", self)
        self.confirm_move_button.clicked.connect(self.on_confirm_move_video_btn_click)
        self.cancel_move_button = QPushButton("跳过该视频", self)
        self.cancel_move_button.clicked.connect(self.on_cancel_move_video_btn_click)

        # Status label at bottom
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("QLabel { color: gray; }")

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.rename_video_frame)
        layout.addWidget(self.move_folder_frame)
        layout.addWidget(self.flatten_folder_frame)
        layout.addWidget(self.folder_path_entry)
        layout.addWidget(self.download_covers_button)
        layout.addWidget(self.magnet_number_entry)
        layout.addWidget(self.fetch_magnets_button)
        layout.addWidget(self.process_button)
        layout.addWidget(self.remove_folder_button)
        layout.addWidget(self.extract_large_videos_button)
        layout.addWidget(self.print_folder_contents_button)
        layout.addWidget(self.start_move_video_folders_button)
        layout.addWidget(self.current_process_video_label)
        layout.addWidget(self.current_video_actor_entry)
        layout.addWidget(self.confirm_move_button)
        layout.addWidget(self.cancel_move_button)
        layout.addWidget(self.status_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def _save_folder_path(self):
        self.settings.setValue("last_folder_path", self.folder_path_entry.text())

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
        file_paths = event.mimeData().numbers()
        file_paths = [path.toLocalFile() for path in file_paths]
        self.rename_service.rename_files(file_paths)

    def on_drop_for_put_into_folders(self, event):
        file_paths = event.mimeData().numbers()
        file_paths = [path.toLocalFile() for path in file_paths]
        self.organize_file_service.sort_and_organize_files(file_paths)

    def on_drop_for_remove_folders(self, event):
        file_path = event.mimeData().numbers()[0].toLocalFile()
        file_path = file_utils.clean_path(file_path)
        self.move_files_to_parent_and_remove_subfolders(file_path)

    def on_download_covers_btn_click(self):
        folder_path = self.folder_path_entry.text()
        self._save_folder_path()
        if not os.path.isdir(folder_path):
            self.status_label.setText("无效的文件夹路径")
            return
        self.download_covers_button.setEnabled(False)
        self.status_label.setText("封面下载中（后台静默进行，每部间隔3秒）...")
        self.cover_worker = CoverDownloadWorker(folder_path)
        self.cover_worker.progress.connect(lambda msg: self.status_label.setText(f'封面: {msg}'))
        self.cover_worker.done.connect(self._on_cover_download_done)
        self.cover_worker.start()

    def on_fetch_magnets_btn_click(self):
        number = self.magnet_number_entry.text().strip().upper()
        if not number:
            self.status_label.setText("请先输入番号")
            return
        self.fetch_magnets_button.setEnabled(False)
        self.status_label.setText(f"正在提取 {number} 的下载信息...")
        self.magnet_worker = MagnetFetchWorker(number)
        self.magnet_worker.done.connect(self._on_magnets_done)
        self.magnet_worker.start()

    def _on_magnets_done(self, number, magnets, error):
        self.fetch_magnets_button.setEnabled(True)
        if error:
            self.status_label.setText(f"{number} 提取失败: {error}")
            return
        self.status_label.setText(f"{number} 共 {len(magnets)} 条下载信息(已打印到控制台)")
        print(f'===== {number} 磁力下载列表 ({len(magnets)} 条) =====')
        for m in magnets:
            print(f'{m["date"]}\t{m["size"]}\t{m["name"]}\n\t{m["magnet"]}')

    def _on_cover_download_done(self, msg):
        self.status_label.setText(msg)
        self.download_covers_button.setEnabled(True)

    def on_move_to_folders_btn_click(self):
        folder_path = self.folder_path_entry.text()
        if os.path.isdir(folder_path):
            file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                          os.path.isfile(os.path.join(folder_path, f))]
            self.organize_file_service.sort_and_organize_files(file_paths)
            print('move finished')
        else:
            print("Invalid folder path")

    def on_remove_folder_btn_click(self):
        folder_path = self.folder_path_entry.text()
        self.move_files_to_parent(folder_path)

    def on_extract_large_videos_btn_click(self):
        folder_path = self.folder_path_entry.text()
        self._save_folder_path()
        if not os.path.isdir(folder_path):
            self.status_label.setText("无效的文件夹路径")
            return
        min_size = 100 * 1024 * 1024  # 100MB
        moved, skipped = 0, 0
        for root, _dirs, files in os.walk(folder_path):
            if os.path.abspath(root) == os.path.abspath(folder_path):
                continue  # only look inside subfolders
            for file in files:
                src = os.path.join(root, file)
                if not file_utils.is_video_file(file):
                    continue
                if os.path.getsize(src) <= min_size:
                    continue
                dst = os.path.join(folder_path, file)
                if os.path.exists(dst):
                    skipped += 1
                    print(f"跳过(根目录已存在同名文件): {src}")
                    continue
                shutil.move(src, dst)
                moved += 1
                print(f"已移动: {src} -> {dst}")
        self.status_label.setText(f"已移动 {moved} 个大视频到根目录，跳过 {skipped} 个(重名)")

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
            
    def on_start_move_videos_btn_click(self):
        print('on_start_move_videos_btn_click')
        folder_path = self.folder_path_entry.text()
        self._save_folder_path()
        if os.path.isdir(folder_path):
            folder_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if
                            os.path.isdir(os.path.join(folder_path, f))]
            self.organize_file_service.start_move_video_folder(folder_paths,
                                                               self.current_process_video_label,
                                                               self.current_video_actor_entry)
        else:
            print("Invalid folder path")

    def on_confirm_move_video_btn_click(self):
        print('move video')
        folder_path = self.folder_path_entry.text()
        if os.path.isdir(folder_path):
            actor_name = self.current_video_actor_entry.text()
            video_name = self.current_process_video_label.text()
            result, error = self.organize_file_service.confirm_move_video_folder(
                video_name, actor_name, folder_path, self.current_video_actor_entry)
            if error:
                self.status_label.setText(f"错误: {error}")
                return
            if result is None:
                return

            source_path, target_path = result
            self._start_move_worker(source_path, target_path)
        else:
            print("Invalid folder path")

    def _start_move_worker(self, source_path, target_path):
        from service.organize_file_service import MoveVideoWorker

        self.confirm_move_button.setEnabled(False)
        self.cancel_move_button.setEnabled(False)

        self.worker = MoveVideoWorker(source_path, target_path)
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.finished.connect(lambda success, msg: self._on_move_finished(success, msg))

        self.worker.start()

    def _on_move_finished(self, success, msg):
        self.status_label.setText(msg)
        self.confirm_move_button.setEnabled(True)
        self.cancel_move_button.setEnabled(True)
        if success:
            self.current_video_actor_entry.setText('==Move Finish==')
        
    def on_cancel_move_video_btn_click(self):
        print('cancel move video')
        folder_path = self.folder_path_entry.text()
        video_name = self.current_process_video_label.text()
        video_folder_path = os.path.join(folder_path, video_name)
        self.organize_file_service.ignore_move_video_folder(video_folder_path)

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