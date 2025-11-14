from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QSlider, QCheckBox, QListWidget, QListWidgetItem, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QMovie, QTransform, QPainter, QIcon
from PyQt5.QtCore import Qt, QSize, QSharedMemory
import sys
import json
import os
import winreg

class OverlayWindow(QWidget):
    def __init__(self, file, config=None, parent=None):
        super().__init__()
        self.file = file
        self.parent_controller = parent
        self.isGif = file.lower().endswith(".gif")
        self.dragging = False
        self.aspect_ratio = None
        self.rotation = 0
        self.opacity_value = 1.0
        self.click_through = False

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        if self.isGif:
            self.movie = QMovie(file)
            self.movie.frameChanged.connect(self.update)
            self.movie.start()
            frame = self.movie.currentPixmap()
            w, h = frame.width(), frame.height()
        else:
            self.pix = QPixmap(file)
            w, h = self.pix.width(), self.pix.height()

        self.aspect_ratio = w / h

        max_side = 350
        if w > max_side or h > max_side:
            scale = max_side / max(w, h)
            w = int(w * scale)
            h = int(h * scale)

        self.original_width = w
        self.original_height = h

        if config:
            self.original_width = config.get('width', w)
            self.original_height = config.get('height', h)
            self.rotation = config.get('rotation', 0)
            self.opacity_value = config.get('opacity', 1.0)
            self.click_through = config.get('click_through', False)
            pos = config.get('position')
            if pos:
                self.move(pos[0], pos[1])

        self.update_window_size()
        self.setWindowOpacity(self.opacity_value)
        self.update_click_through()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation)
        painter.translate(-self.original_width / 2, -self.original_height / 2)

        if self.isGif:
            frame = self.movie.currentPixmap()
            pix = frame
        else:
            pix = self.pix

        scaled_pix = pix.scaled(self.original_width, self.original_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_pix)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.click_through:
            self.dragging = True
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and not self.click_through:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        if self.parent_controller:
            self.parent_controller.restore_z_order()
        event.accept()

    def wheelEvent(self, event):
        if self.click_through:
            return
            
        delta = event.angleDelta().y()

        if QApplication.mouseButtons() & Qt.LeftButton:
            scale_factor = 1 + (delta / 1000)
            self.original_width = max(50, int(self.original_width * scale_factor))
            self.original_height = int(self.original_width / self.aspect_ratio)
            self.update_window_size()

        elif QApplication.mouseButtons() & Qt.RightButton:
            self.rotation += delta / 10
            self.rotation %= 360
            self.update_window_size()
    
    def update_window_size(self):
        """Resize window to fit rotated image"""
        import math
        
        angle_rad = math.radians(self.rotation)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))
        
        new_width = int(self.original_width * cos_a + self.original_height * sin_a)
        new_height = int(self.original_width * sin_a + self.original_height * cos_a)
        
        self.setFixedSize(new_width, new_height)
        self.update()

    def set_opacity(self, value):
        """Set opacity (0-100)"""
        self.opacity_value = value / 100
        self.setWindowOpacity(self.opacity_value)

    def set_click_through(self, enabled):
        """Enable/disable click-through mode"""
        self.click_through = enabled
        self.update_click_through()

    def update_click_through(self):
        """Update window flags for click-through"""
        if self.click_through:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def get_config(self):
        """Return current configuration for saving"""
        pos = self.pos()
        return {
            'file': self.file,
            'width': self.original_width,
            'height': self.original_height,
            'rotation': self.rotation,
            'opacity': self.opacity_value,
            'click_through': self.click_through,
            'position': [pos.x(), pos.y()]
        }

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.overlays = []
        self.file = None
        
        app_data = os.path.join(os.environ['APPDATA'], 'DesktopOverlay')
        os.makedirs(app_data, exist_ok=True)
        
        self.config_file = os.path.join(app_data, 'overlay_config.json')
        self.settings_file = os.path.join(app_data, 'overlay_settings.json')
        self.app_name = "DesktopOverlay"

        self.setWindowTitle("Overlay Controller")
        self.setFixedWidth(320)

        self.load_settings()
        
        self.cleanup_old_startup_entries()

        self.setup_tray()

        layout = QVBoxLayout()

        self.preview = QLabel("No Image Selected")
        self.preview.setFixedSize(250, 250)
        self.preview.setStyleSheet("background: #222; color: white; border: 1px solid #555;")
        self.preview.setAlignment(Qt.AlignCenter)

        btnLayout = QHBoxLayout()
        self.btnChoose = QPushButton("Choose Image/GIF")
        self.btnChoose.clicked.connect(self.choose_file)
        btnLayout.addWidget(self.btnChoose)

        opacityLayout = QHBoxLayout()
        opacityLabel = QLabel("Opacity:")
        self.opacitySlider = QSlider(Qt.Horizontal)
        self.opacitySlider.setMinimum(10)
        self.opacitySlider.setMaximum(100)
        self.opacitySlider.setValue(100)
        self.opacitySlider.valueChanged.connect(self.update_opacity)
        self.opacityValue = QLabel("100%")
        opacityLayout.addWidget(opacityLabel)
        opacityLayout.addWidget(self.opacitySlider)
        opacityLayout.addWidget(self.opacityValue)

        self.clickThroughCheck = QCheckBox("Click-through mode")
        self.clickThroughCheck.stateChanged.connect(self.toggle_click_through)

        self.btnStart = QPushButton("Add New Overlay")
        self.btnStart.clicked.connect(self.start_overlay)

        listLabel = QLabel("Active Overlays:")
        self.overlayList = QListWidget()
        self.overlayList.setMaximumHeight(200)
        self.overlayList.setIconSize(QSize(60, 60))
        self.overlayList.setDragDropMode(QListWidget.InternalMove)
        self.overlayList.model().rowsMoved.connect(self.on_list_reorder)

        listBtnLayout = QHBoxLayout()
        self.btnRemove = QPushButton("Remove Selected")
        self.btnRemoveAll = QPushButton("Remove All")
        self.btnRemove.clicked.connect(self.remove_selected)
        self.btnRemoveAll.clicked.connect(self.remove_all)
        listBtnLayout.addWidget(self.btnRemove)
        listBtnLayout.addWidget(self.btnRemoveAll)

        saveBtnLayout = QHBoxLayout()
        self.btnSave = QPushButton("Save Layout")
        self.btnLoad = QPushButton("Load Layout")
        self.btnSave.clicked.connect(self.save_layout)
        self.btnLoad.clicked.connect(self.load_layout)
        saveBtnLayout.addWidget(self.btnSave)
        saveBtnLayout.addWidget(self.btnLoad)

        settingsLabel = QLabel("Settings:")
        self.autoLoadCheck = QCheckBox("Auto-load layout on startup")
        self.autoLoadCheck.setChecked(self.auto_load_layout)
        self.autoLoadCheck.stateChanged.connect(self.toggle_auto_load)
        
        self.autoStartCheck = QCheckBox("Run at Windows startup")
        self.autoStartCheck.setChecked(self.is_in_startup())
        self.autoStartCheck.stateChanged.connect(self.toggle_auto_start)

        layout.addWidget(self.preview)
        layout.addLayout(btnLayout)
        layout.addLayout(opacityLayout)
        layout.addWidget(self.clickThroughCheck)
        layout.addWidget(self.btnStart)
        layout.addWidget(listLabel)
        layout.addWidget(self.overlayList)
        layout.addLayout(listBtnLayout)
        layout.addLayout(saveBtnLayout)
        layout.addWidget(settingsLabel)
        layout.addWidget(self.autoLoadCheck)
        layout.addWidget(self.autoStartCheck)

        self.setLayout(layout)

        if self.auto_load_layout and os.path.exists(self.config_file):
            self.load_layout()

    def choose_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.gif)"
        )
        if not file:
            return

        self.file = file

        if file.lower().endswith(".gif"):
            movie = QMovie(file)
            movie.setScaledSize(self.preview.size())
            self.preview.setMovie(movie)
            movie.start()
        else:
            pix = QPixmap(file)
            scaled = pix.scaled(
                self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview.setPixmap(scaled)

    def start_overlay(self):
        if self.file:
            overlay = OverlayWindow(self.file, parent=self)
            overlay.set_opacity(self.opacitySlider.value())
            overlay.set_click_through(self.clickThroughCheck.isChecked())
            overlay.show()
            self.overlays.append(overlay)
            self.update_overlay_list()
            self.restore_z_order()

    def update_opacity(self, value):
        self.opacityValue.setText(f"{value}%")
        for overlay in self.overlays:
            overlay.set_opacity(value)

    def toggle_click_through(self, state):
        enabled = state == Qt.Checked
        for overlay in self.overlays:
            overlay.set_click_through(enabled)

    def update_overlay_list(self):
        self.overlayList.clear()
        for i, overlay in enumerate(self.overlays):
            filename = os.path.basename(overlay.file)
            
            if overlay.isGif:
                thumbnail = overlay.movie.currentPixmap()
            else:
                thumbnail = QPixmap(overlay.file)
            
            thumbnail = thumbnail.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            item = QListWidgetItem(f"{i+1}. {filename}")
            item.setIcon(QIcon(thumbnail))
            self.overlayList.addItem(item)
    
    def on_list_reorder(self):
        """Handle drag-and-drop reordering of overlays"""
        new_order = []
        for i in range(self.overlayList.count()):
            item_text = self.overlayList.item(i).text()
            original_index = int(item_text.split('.')[0]) - 1
            new_order.append(original_index)
        
        self.overlays = [self.overlays[i] for i in new_order]
        
        self.restore_z_order()
        self.update_overlay_list()
    
    def restore_z_order(self):
        """Restore z-order based on list position (bottom to top)"""
        for overlay in self.overlays:
            overlay.raise_()

    def remove_selected(self):
        current_row = self.overlayList.currentRow()
        if current_row >= 0 and current_row < len(self.overlays):
            overlay = self.overlays[current_row]
            overlay.close()
            self.overlays.pop(current_row)
            self.update_overlay_list()

    def remove_all(self):
        for overlay in self.overlays:
            overlay.close()
        self.overlays.clear()
        self.update_overlay_list()

    def save_layout(self):
        """Save all overlay positions and settings"""
        config = {
            'overlays': [overlay.get_config() for overlay in self.overlays]
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Layout saved to {self.config_file}")
            self.tray_icon.showMessage(
                "Layout Saved",
                f"Saved {len(self.overlays)} overlay(s)",
                QSystemTrayIcon.Information,
                2000
            )
        except Exception as e:
            print(f"Error saving layout: {e}")

    def load_layout(self):
        """Load overlay positions and settings"""
        if not os.path.exists(self.config_file):
            print(f"No saved layout found at {self.config_file}")
            self.tray_icon.showMessage(
                "No Layout Found",
                "No saved layout to load",
                QSystemTrayIcon.Warning,
                2000
            )
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.remove_all()
            
            loaded_count = 0
            for overlay_config in config.get('overlays', []):
                if os.path.exists(overlay_config['file']):
                    overlay = OverlayWindow(overlay_config['file'], overlay_config, parent=self)
                    overlay.show()
                    self.overlays.append(overlay)
                    loaded_count += 1
                else:
                    print(f"Image file not found: {overlay_config['file']}")
            
            self.restore_z_order()
            self.update_overlay_list()
            print(f"Layout loaded: {loaded_count} overlay(s) from {self.config_file}")
            
            if loaded_count > 0:
                self.tray_icon.showMessage(
                    "Layout Loaded",
                    f"Loaded {loaded_count} overlay(s)",
                    QSystemTrayIcon.Information,
                    2000
                )
        except Exception as e:
            print(f"Error loading layout: {e}")

    def setup_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        icon = self.get_app_icon()
        self.tray_icon.setIcon(icon)
        
        self.setWindowIcon(icon)
        
        tray_menu = QMenu()
        
        show_action = QAction("Show Controller", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide Controller", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def get_app_icon(self):
        """Get application icon"""
        icon_paths = ['Ameno.ico', 'icon.ico']
        
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            icon_paths = [os.path.join(bundle_dir, 'Ameno.ico'), 
                         os.path.join(bundle_dir, 'icon.ico')] + icon_paths
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.blue)
        return QIcon(pixmap)

    def tray_icon_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()

    def quit_application(self):
        """Properly quit the application"""
        self.remove_all()
        self.tray_icon.hide()
        QApplication.quit()

    def load_settings(self):
        """Load application settings"""
        self.auto_load_layout = False
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.auto_load_layout = settings.get('auto_load_layout', False)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save application settings"""
        settings = {
            'auto_load_layout': self.auto_load_layout
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def toggle_auto_load(self, state):
        """Toggle auto-load layout setting"""
        self.auto_load_layout = state == Qt.Checked
        self.save_settings()

    def is_in_startup(self):
        """Check if app is in Windows startup"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                current_exe = os.path.abspath(sys.argv[0])
                return value.strip('"') == current_exe
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            print(f"Error checking startup: {e}")
            return False

    def cleanup_old_startup_entries(self):
        """Remove old/duplicate startup entries"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_ALL_ACCESS)
            
            current_exe = os.path.abspath(sys.argv[0])
            
            old_names = ["OverlayController", "DesktopOverlay by Ameno", "Desktop Overlay"]
            
            for old_name in old_names:
                if old_name != self.app_name:
                    try:
                        winreg.DeleteValue(key, old_name)
                        print(f"Removed old startup entry: {old_name}")
                    except FileNotFoundError:
                        pass
            
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                if value.strip('"') != current_exe:
                    winreg.DeleteValue(key, self.app_name)
                    print(f"Removed outdated startup entry for {self.app_name}")
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error cleaning up startup entries: {e}")

    def toggle_auto_start(self, state):
        """Toggle Windows startup"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_WRITE)
            
            if state == Qt.Checked:
                exe_path = os.path.abspath(sys.argv[0])
                if ' ' in exe_path:
                    exe_path = f'"{exe_path}"'
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
                print(f"Added to startup: {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    print("Removed from startup")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error toggling startup: {e}")

    def closeEvent(self, event):
        """Minimize to tray instead of closing"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Overlay Controller",
            "Application minimized to system tray",
            QSystemTrayIcon.Information,
            2000
        )


app = QApplication(sys.argv)

shared_memory = QSharedMemory("DesktopOverlayApp")
if not shared_memory.create(1):
    print("Application is already running!")
    sys.exit(0)

app.setQuitOnLastWindowClosed(False)
window = MainWindow()
window.show()
sys.exit(app.exec_())