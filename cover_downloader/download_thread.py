import sys
import os
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QWidget, QLabel, QProgressBar,
                             QMessageBox, QFileDialog, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
import urllib.parse
import file_utils


class DownloadThread(QThread):
    """Thread for downloading images to avoid freezing the UI"""
    progress_signal = pyqtSignal(int, int, str)  # current, total, status
    finished_signal = pyqtSignal(bool, str, str)  # success, url, message
    
    def __init__(self, numbers, download_folder=None):
        super().__init__()
        self.url_templates = [
            f"https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/[series]00[digit]/[series]00[digit]pl.jpg",
            f"https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/[series][digit]/[series][digit]pl.jpg",
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/video/[series][digit]/[series][digit]pl.jpg",
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/video/[series]00[digit]/[series]00[digit]pl.jpg",
        ]
        self.prefix_star = "1"
        self.prefix_abp = "118"
        self.url_star_templates = [
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/movie/{self.prefix_star}[series][digit]/{self.prefix_star}[series][digit]pl.jpg",
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/movie/{self.prefix_star}[series]00[digit]/{self.prefix_star}[series]00[digit]pl.jpg"
        ]

        self.url_prefix = "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/"
        self.url_suffix = "pl.jpg"
        self.numbers = numbers
        self.download_folder = "/Users/vincent/Downloads/JAV_Covers"
        self.failed_list = [
            "HODV-21066",
            "DV-1649",
            "REBD-700",
            "SDHS-059",
            "ORECO-408",
            "SDHS-059",
            "GVG-102",
            "GVG-868",
            "VDD-123",
            "YSN-414",
            "MDB-601",
            "ONGP-027",
            "XVSR-013",
            "UMAD-085",
            "FSET-557A",
            "MKD-S128",
            "LXVS-036",
        ]
        
    def _get_url_template(self, prefix):
        return [
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/movie/{prefix}[series][digit]/{prefix}[series][digit]pl.jpg",
            f"https://awsimgsrc.dmm.co.jp/pics_dig/mono/movie/{prefix}[series]00[digit]/{prefix}[series]00[digit]pl.jpg"
        ]
        
    def _get_urls_from_number(self, number):
        parts = number.lower().split("-")
        series: str = parts[0]
        digit: str = parts[1]
        urls = []
        url_templates = self.url_templates
        if series.startswith("star") or series.startswith("sdde"):
            url_templates = self._get_url_template(self.prefix_star)
        elif series == "abp":
            url_templates = self._get_url_template(self.prefix_abp)
        for url_template in url_templates:
            url = url_template.replace('[series]', series)
            url = url.replace('[digit]', digit)
            urls.append(url)
        return urls
    
    def run(self):
        total = len(self.numbers)
        for i, number in enumerate(self.numbers):
            if not number.strip():
                continue
            
            filename = f"{number}.jpg"
            save_path = os.path.join(self.download_folder, filename)
            
            if os.path.exists(save_path):
                self.finished_signal.emit(True, number, f"Skip: {filename}")
                continue
            
            self.progress_signal.emit(i + 1, total, f"Downloading: {number}")
            
            try:
                
                # Extract filename from URL or generate one
                urls = self._get_urls_from_number(number)
                for url in urls:
                    # Download the image
                    success = self.download_image(url, save_path)
                    if success:
                        self.finished_signal.emit(True, number, f"Success: {filename}")
                        break
                    else:
                        self.finished_signal.emit(False, number, f"Failed: {number}")
            
            except Exception as e:
                self.finished_signal.emit(False, number, f"Error: {str(e)}")
    
    def download_image(self, url, save_path):
        """Download image function with placeholder image check"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if 'image' not in response.headers.get('Content-Type', ''):
                return False
            
            # Check image size before saving
            image_size = len(response.content)
            min_size = 50 * 1024  # 50KB in bytes
            
            if image_size < min_size:
                print(f"Image too small ({image_size} bytes < {min_size} bytes) - likely a placeholder")
                return False
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded image: {os.path.basename(save_path)} ({image_size} bytes)")
            return True
        
        except Exception as e:
            print(f"Download error: {e}")
            return False