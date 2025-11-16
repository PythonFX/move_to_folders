import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QPushButton, \
    QProgressBar, QFileDialog, QMessageBox, QApplication, QLineEdit

from cover_downloader.download_thread import DownloadThread


class ImageDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_thread = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Image Downloader")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Image URL Downloader")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # NEW: Directory browser section
        dir_label = QLabel("Browse Directory:")
        dir_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(dir_label)
        
        # Directory input row
        dir_layout = QHBoxLayout()
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Enter directory path or click 'Browse' to select...")
        self.dir_input.textChanged.connect(self.on_dir_input_changed)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_directory)
        
        self.confirm_button = QPushButton("List Subfolders")
        self.confirm_button.clicked.connect(self.list_subfolders)
        self.confirm_button.setEnabled(False)  # Disabled until valid path
        
        dir_layout.addWidget(QLabel("Directory:"))
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.browse_button)
        dir_layout.addWidget(self.confirm_button)
        
        layout.addLayout(dir_layout)
        
        # Instructions
        instructions = QLabel("Enter one image URL per line:")
        instructions.setFont(QFont("Arial", 10))
        layout.addWidget(instructions)
        
        # URL input area
        self.url_textedit = QTextEdit()
        self.url_textedit.setPlaceholderText(
            "Enter video Number here, one per line...\nExample:\nSSIS-778\nIPZZ-077\nABP-542")
        self.url_textedit.setMinimumHeight(150)
        layout.addWidget(self.url_textedit)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Download folder selection
        self.folder_label = QLabel("Download folder: ./downloads")
        self.folder_button = QPushButton("Change Folder")
        self.folder_button.clicked.connect(self.select_download_folder)
        
        controls_layout.addWidget(self.folder_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.folder_button)
        
        layout.addLayout(controls_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Start Download")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        
        self.clear_button = QPushButton("Clear URLs")
        self.clear_button.clicked.connect(self.clear_urls)
        self.clear_button.setStyleSheet("QPushButton { padding: 8px; }")
        
        buttons_layout.addWidget(self.download_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress counters
        self.progress_counters = QLabel("")
        self.progress_counters.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_counters)
        
        # Log area
        log_label = QLabel("Download Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(log_label)
        
        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setMaximumHeight(200)
        layout.addWidget(self.log_textedit)
        
        # Set default download folder
        self.download_folder = "./downloads"
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Counters for statistics
        self.success_count = 0
        self.failure_count = 0
    
    def on_dir_input_changed(self, text):
        """Enable/disable confirm button based on path validity"""
        if text and os.path.exists(text) and os.path.isdir(text):
            self.confirm_button.setEnabled(True)
            self.confirm_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        else:
            self.confirm_button.setEnabled(False)
            self.confirm_button.setStyleSheet("")
    
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)
    
    def list_subfolders(self):
        """List all immediate subfolders of the specified directory"""
        directory_path = self.dir_input.text().strip()
        
        if not directory_path:
            self.add_log("✗ Please enter a directory path", QColor(255, 0, 0))
            return
        
        if not os.path.exists(directory_path):
            self.add_log(f"✗ Directory does not exist: {directory_path}", QColor(255, 0, 0))
            return
        
        if not os.path.isdir(directory_path):
            self.add_log(f"✗ Path is not a directory: {directory_path}", QColor(255, 0, 0))
            return
        
        try:
            # get all actor folders in the root directory
            actor_paths = []
            for actor in os.listdir(directory_path):
                if actor.startswith("."):
                    continue
                path = os.path.join(directory_path, actor)
                if os.path.isdir(path):
                    actor_paths.append(path)
            
            items = []
            for actor_path in actor_paths:
                # Get all items in the directory
                for item in os.listdir(actor_path):
                    if item.startswith("."):
                        continue
                    path = os.path.join(actor_path, item)
                    if os.path.isdir(path):
                        items.append(item)
            
            # Filter only subdirectories (one level, no recursion)
            video_numbers = []
            for item in items:
                print(item)
                number_part = item.split(" ")[0]
                if "[4K]" in number_part:
                    number_part = number_part.replace("[4K]", "")
                video_numbers.append(number_part)
            
            self._download_numbers(video_numbers)
        except PermissionError:
            self.add_log(f"✗ Permission denied accessing: {directory_path}", QColor(255, 0, 0))
        except Exception as e:
            self.add_log(f"✗ Error reading directory: {str(e)}", QColor(255, 0, 0))
    
    def select_download_folder(self):
        """Open dialog to select download folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder
            self.folder_label.setText(f"Download folder: {folder}")
    
    def start_download(self):
        """Start downloading images"""
        number_texts = self.url_textedit.toPlainText().strip()
        if not number_texts:
            QMessageBox.warning(self, "Warning", "Please enter at least one Number")
            return
        
        numbers = [url.strip() for url in number_texts.split('\n') if url.strip()]
        
        if not numbers:
            QMessageBox.warning(self, "Warning", "No valid Numbers found")
            return
        self._download_numbers(numbers)
        
    def _download_numbers(self, numbers):
        # Disable download button during download
        self.download_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Setup progress bar
        self.progress_bar.setMaximum(len(numbers))
        self.progress_bar.setValue(0)
        
        # Clear log
        self.log_textedit.clear()
        
        # Create and start download thread
        self.download_thread = DownloadThread(numbers, self.download_folder)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.start()
        
        self.add_log(f"Starting download of {len(numbers)} images...")
    
    def update_progress(self, current, total, status):
        """Update progress bar and status"""
        self.progress_bar.setValue(current)
        self.status_label.setText(status)
    
    def download_finished(self, success, url, message):
        """Handle completion of individual download"""
        if success:
            self.add_log(f"✓ {message}", QColor(0, 255, 0))
        else:
            self.add_log(f"✗ {message}", QColor(255, 0, 0))
        
        # Check if all downloads are complete
        if self.progress_bar.value() == self.progress_bar.maximum():
            self.download_complete()
    
    def download_complete(self):
        """Handle completion of all downloads"""
        self.download_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.status_label.setText("Download completed!")
        
        QMessageBox.information(self, "Complete", "All downloads completed!")
    
    def add_log(self, message, color: QColor=None):
        """Add message to log with timestamp and optional color"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        cursor = self.log_textedit.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set text color if specified
        if color:
            format = QTextCharFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)
        
        cursor.insertText(log_entry + '\n')
        
        # Reset to default color
        default_format = QTextCharFormat()
        default_format.setForeground(QColor(0, 0, 0))  # Black
        cursor.setCharFormat(default_format)
        
        # Auto-scroll to bottom
        self.log_textedit.setTextCursor(cursor)
        self.log_textedit.ensureCursorVisible()
    
    def clear_urls(self):
        """Clear the URL input area"""
        self.url_textedit.clear()
        self.log_textedit.clear()
        self.status_label.setText("Ready")
        self.progress_bar.setVisible(False)
