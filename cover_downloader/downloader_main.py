import sys
from PyQt5.QtWidgets import (QApplication)

from cover_downloader.image_downloader_app import ImageDownloaderApp


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = ImageDownloaderApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()