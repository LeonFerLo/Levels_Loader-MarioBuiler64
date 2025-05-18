from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QComboBox, QLabel, QDialog, QDialogButtonBox,
                            QPushButton, QFileDialog, QHBoxLayout, QSpacerItem,
                            QSizePolicy)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl, QDir, QStorageInfo
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import sys
import os
import urllib.parse
from PyQt5.QtWidgets import QMessageBox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtGui import QIcon


class DiskSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        if os.path.exists("mb64.ico"):  # Busca el icono en formato .ico
            self.setWindowIcon(QIcon("mb64.ico"))
        else:
            print("No se encontró el archivo de icono (mb64_logo.ico o mb64_logo.png)")
        self.setWindowTitle("Seleccionar unidad de disco")

        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        label = QLabel(
            "Seleccione la sd virtual de su emulador, donde se guardarán los niveles\n\n"
            "Recuerda que tienes que cargar la sd virtual desde Parallel Launcher\n"
            "Puedes configurarla y darle a 'Explorar archivos' para activarla\n"
            "deveria se como AUTO0, o algo asi"
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        self.disk_combo = QComboBox()
        self.populate_disks()
        layout.addWidget(self.disk_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def populate_disks(self):
        disks = QStorageInfo.mountedVolumes()
        for disk in disks:
            if disk.isValid() and disk.isReady():
                self.disk_combo.addItem(f"{disk.rootPath()} ({disk.displayName()})", disk.rootPath())

def get_level_title(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        title_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.title-card span.level-title"))
        )
        title = title_element.text.strip()
        driver.quit()
        return title
    except Exception as e:
        print(f"[Selenium] Error obteniendo título: {e}")
        return None

class Navegador(QMainWindow):
    def __init__(self):
        super().__init__()
        if os.path.exists("mb64.ico"):  # Busca el icono en formato .ico
            self.setWindowIcon(QIcon("mb64.ico"))
        else:
            print("No se encontró el archivo de icono (mb64_logo.ico o mb64_logo.png)")
        disk_dialog = DiskSelector()
        if disk_dialog.exec_() != QDialog.Accepted:
            sys.exit(0)
        
        selected_disk = disk_dialog.disk_combo.currentData()
        self.download_path = os.path.join(selected_disk, "Mario Builder 64 Levels")
        QDir().mkpath(self.download_path)
        
        self.setWindowTitle("MB64 - Levels Loader")
        self.setGeometry(100, 100, 1024, 768)
        
        # Crear widget central y layout
        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear barra de herramientas con botón de carga
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)  # Márgenes internos
        
        # 1. Botón Atrás (tamaño compacto)
        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(40, 30)  # Tamaño fijo pequeño
        self.back_button.setToolTip("Volver atrás")
        self.back_button.clicked.connect(self.go_back)
        toolbar_layout.addWidget(self.back_button)
        
        # 4. Espaciador central
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 5. Botón Cargar (tamaño proporcional)
        self.upload_button = QPushButton("Cargar Nivel")
        self.upload_button.setMinimumWidth(120)  # Ancho mínimo
        self.upload_button.setMaximumWidth(200)  # Ancho máximo
        self.upload_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.upload_button.clicked.connect(self.upload_file)
        toolbar_layout.addWidget(self.upload_button)
        
        # Configuración final de la barra
        toolbar.setLayout(toolbar_layout)
        toolbar.setFixedHeight(50)  # Altura fija para toda la barra
        main_layout.addWidget(toolbar)
        
        # Añadir el navegador
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://levelsharesquare.com/MB64/levels"))
        main_layout.addWidget(self.browser)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.handle_download)
        
        self.browser.loadFinished.connect(self.inject_css)
    def resizeEvent(self, event):
        """Ajusta dinámicamente el ancho del botón"""
        button_width = min(200, self.width() // 4)  # Máximo 200px o 25% del ancho
        self.upload_button.setFixedWidth(button_width)
        super().resizeEvent(event)
    def go_back(self):
        """Navega a la página anterior en el historial"""
        if self.browser.history().canGoBack():
            self.browser.back()
    def resizeEvent(self, event):
        # Actualizar el ancho del botón cuando se redimensiona la ventana
        self.upload_button.setFixedWidth(int(self.width()/2))
        super().resizeEvent(event)
    
    def upload_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Seleccionar archivo MB64", 
                "", 
                "Archivos MB64 (*.mb64);;Todos los archivos (*)"
            )
            
            if file_path:
                filename = os.path.basename(file_path)
                destination = os.path.join(self.download_path, filename)
                
                import shutil
                shutil.copy2(file_path, destination)
                
                QMessageBox.information(
                    self, 
                    "Archivo cargado", 
                    f"El archivo {filename} se ha copiado correctamente a:\n{destination}"
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"No se pudo cargar el archivo:\n{str(e)}"
            )
    
    def handle_download(self, download: QWebEngineDownloadItem):
        try:
            url = self.browser.url().toString()
            parsed_url = urllib.parse.urlparse(url)
            
            print(f"Obteniendo título desde: {url}")
            title = get_level_title(url)
            print(f"Título obtenido: {title}")
            
            if title:
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
                filename = f"{safe_title}.mb64"
            else:
                filename = os.path.basename(parsed_url.path)
                if not filename.endswith(".mb64"):
                    filename += ".mb64"
            
            download_path = os.path.join(self.download_path, filename)
            QDir().mkpath(self.download_path)
            
            download.setPath(download_path)
            download.accept()
            
            download.finished.connect(lambda: self.download_finished(download_path))
        
        except Exception as e:
            print(f"[PyQt] Error al manejar descarga: {e}")
    
    def download_finished(self, path):
        print(f"Descarga completada correctamente en: {path}")
        QMessageBox.information(self, "Descarga completa", f"La descarga ha finalizado")
    
    def inject_css(self, ok):
        if ok:
            css = """
            .register-bar, .user-bar, .navbar, header, nav {
                display: none !important;
            }
            body {
                padding-top: 0 !important;
            }
            """
            js = f"""
            var style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = `{css}`;
            document.head.appendChild(style);
            """
            self.browser.page().runJavaScript(js)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        from PyQt5 import QtWebEngineWidgets
    except ImportError:
        print("Error: PyQtWebEngine no está instalado.")
        sys.exit(1)
    
    ventana = Navegador()
    ventana.show()
    sys.exit(app.exec_())