import sys
import os,shutil
import zipfile
import xml.etree.ElementTree as ET
import urllib.parse
import chardet
import datetime
from tempfile import TemporaryDirectory

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QTextEdit, QStatusBar, QMessageBox,
    QInputDialog, QVBoxLayout, QWidget, QGroupBox, QLineEdit,
    QPushButton, QLabel, QFormLayout
)
from PyQt6.QtCore import QUrl, Qt, QTimer, QSettings
from PyQt6.QtGui import QAction, QTextCursor, QTextDocument
from PyQt6.QtWebEngineWidgets import QWebEngineView
from converter.html2txt import Maindehtml2txt
from converter.txt2html2 import MaindeTxt2Html
from converter.HTML2EPUB.GenerateEpubFramework import MaindeGenerateEpubFramework
from converter.HTML2EPUB.GenerateEPUB import MaindeGenerateEPUB





class EpubParser:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.temp_dir = TemporaryDirectory()
        self.opf_path = None
        self.spine_items = []
        self.manifest = {}
        self.title = "Untitled"
        
        self.extract_epub()
        self.parse_container()
        self.parse_opf()

    def extract_epub(self):
        with zipfile.ZipFile(self.epub_path, 'r') as zf:
            zf.extractall(self.temp_dir.name)

    def parse_container(self):
        container_path = os.path.join(self.temp_dir.name, 'META-INF', 'container.xml')
        tree = ET.parse(container_path)
        ns = {'ns': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfile = tree.find('.//ns:rootfile', ns)
        if rootfile is not None:
            self.opf_path = os.path.join(self.temp_dir.name, 
                                       urllib.parse.unquote(rootfile.attrib['full-path']))

    def parse_opf(self):
        opf_dir = os.path.dirname(self.opf_path)
        tree = ET.parse(self.opf_path)
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        metadata = tree.find('opf:metadata', ns)
        if metadata is not None:
            title_elem = metadata.find('dc:title', ns)
            if title_elem is not None:
                self.title = title_elem.text
                
        manifest = tree.find('opf:manifest', ns)
        for item in manifest.findall('opf:item', ns):
            item_id = item.attrib['id']
            href = urllib.parse.unquote(item.attrib['href'])
            full_path = os.path.normpath(os.path.join(opf_dir, href))
            self.manifest[item_id] = {
                'path': full_path,
                'type': item.attrib.get('media-type', '')
            }
        
        spine = tree.find('opf:spine', ns)
        for itemref in spine.findall('opf:itemref', ns):
            item_id = itemref.attrib['idref']
            if item_id in self.manifest:
                item = self.manifest[item_id]
                if item['type'] in ['application/xhtml+xml', 'text/html']:
                    self.spine_items.append(item['path'])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.default_txt_dir = os.path.join(os.getcwd(), 'primary fileSet', 'txt')
        os.makedirs(self.default_txt_dir, exist_ok=True)  # 确保目录存在
        self.epub_parser = None
        self.current_text_file = None
        self.text_saved = True
        self.settings = QSettings(QSettings.Format.IniFormat, 
                            QSettings.Scope.UserScope, 
                            "YourCompany", "YourApp")
        self.init_ui()
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.start(30000)
        self.auto_save_timer.timeout.connect(self.auto_save)

    def init_ui(self):
        self.setWindowTitle('epubManager')
        self.setGeometry(100, 100, 1024, 768)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # EPUB阅读器标签页
        self.epub_splitter = QSplitter()
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.itemClicked.connect(self.load_content)
        self.web_view = QWebEngineView()
        self.epub_splitter.addWidget(self.toc_tree)
        self.epub_splitter.addWidget(self.web_view)
        self.epub_splitter.setSizes([200, 824])
        epub_tab = QWidget()
        epub_tab.setLayout(QVBoxLayout())
        epub_tab.layout().addWidget(self.epub_splitter)
        
        # 文本编辑器标签页
        self.text_edit = QTextEdit()
        self.text_edit.setUndoRedoEnabled(True)
        self.text_edit.textChanged.connect(self.mark_unsaved_changes)
        editor_tab = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.text_edit)
        editor_tab.setLayout(editor_layout)
        
        self.tab_widget.addTab(epub_tab, "EPUB阅读器")
        self.tab_widget.addTab(editor_tab, "文本编辑器")
        self.setCentralWidget(self.tab_widget)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建菜单
        self.create_menus()
        
        # 恢复设置
        self.restore_settings()
        self.setup_conversion_tab()

    def setup_conversion_tab(self):
        conversion_tab = QWidget()
        layout = QVBoxLayout()

        # EPUB转TXT分组
        epub_to_txt_group = QGroupBox("EPUB转TXT")
        epub_to_txt_layout = QFormLayout()
        
        self.epub_path_edit = QLineEdit()
        self.epub_path_edit.setReadOnly(True)
        epub_browse_btn = QPushButton("选择EPUB文件")
        epub_browse_btn.clicked.connect(self.select_epub_for_conversion)
        
        self.chapters_edit = QLineEdit()
        self.chapters_edit.setPlaceholderText("输入章节号（如1,3,5），留空转换全部")
        
        convert_epub_btn = QPushButton("开始转换")
        convert_epub_btn.clicked.connect(self.convert_epub_to_txt)
        
        epub_to_txt_layout.addRow(QLabel("EPUB文件:"), self.epub_path_edit)
        epub_to_txt_layout.addRow(epub_browse_btn)
        epub_to_txt_layout.addRow(QLabel("章节选择:"), self.chapters_edit)
        epub_to_txt_layout.addRow(convert_epub_btn)
        epub_to_txt_group.setLayout(epub_to_txt_layout)

        # TXT转HTML分组
        txt_to_html_group = QGroupBox("TXT转HTML")
        txt_to_html_layout = QFormLayout()
        
        self.txt_file_edit = QLineEdit()
        self.txt_file_edit.setReadOnly(True)
        txt_browse_btn = QPushButton("选择TXT文件")
        txt_browse_btn.clicked.connect(self.select_txt_for_conversion)
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("输入输出目录名，也就是决定将你写的这一章插到哪一个epub框架里（还记得你之前的命名吗？）")
        
        convert_txt_btn = QPushButton("开始转换")
        convert_txt_btn.clicked.connect(self.convert_txt_to_html)
        
        txt_to_html_layout.addRow(QLabel("TXT文件:"), self.txt_file_edit)
        txt_to_html_layout.addRow(txt_browse_btn)
        txt_to_html_layout.addRow(QLabel("输出目录:"), self.output_dir_edit)
        txt_to_html_layout.addRow(convert_txt_btn)
        txt_to_html_group.setLayout(txt_to_html_layout)

        # 生成EPUB框架分组
        framework_group = QGroupBox("创建EPUB框架")
        framework_layout = QFormLayout()
        
        self.framework_name_edit = QLineEdit()
        self.framework_name_edit.setPlaceholderText("输入框架名称，也就是给建的新epub框架取名字（默认：第一个）")
        
        create_framework_btn = QPushButton("创建框架")
        create_framework_btn.clicked.connect(self.create_epub_framework)
        
        framework_layout.addRow(QLabel("框架名称:"), self.framework_name_edit)
        framework_layout.addRow(create_framework_btn)
        framework_group.setLayout(framework_layout)

        # 生成EPUB分组
        generate_epub_group = QGroupBox("生成EPUB文件")
        generate_layout = QFormLayout()
        
        self.source_folder_edit = QLineEdit()
        self.source_folder_edit.setPlaceholderText("输入源文件夹名，也就是指定哪个epub框架去生成epub文件（默认：第一个）")
        
        self.epub_name_edit = QLineEdit()
        self.epub_name_edit.setPlaceholderText("输入输出文件名，也就是给你的新epub文件（成了）取名字（默认：example.epub）")
        
        generate_btn = QPushButton("生成EPUB")
        generate_btn.clicked.connect(self.generate_epub)
        
        generate_layout.addRow(QLabel("源文件夹:"), self.source_folder_edit)
        generate_layout.addRow(QLabel("输出文件:"), self.epub_name_edit)
        generate_layout.addRow(generate_btn)
        generate_epub_group.setLayout(generate_layout)

        layout.addWidget(epub_to_txt_group)
        layout.addWidget(txt_to_html_group)
        layout.addWidget(framework_group)
        layout.addWidget(generate_epub_group)
        layout.addStretch()
        
        conversion_tab.setLayout(layout)
        self.tab_widget.addTab(conversion_tab, "转换工具")

    def select_epub_for_conversion(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择EPUB文件", "", "EPUB文件 (*.epub)")
        if path:
            self.epub_path_edit.setText(path)

    def convert_epub_to_txt(self):
        epub_path = self.epub_path_edit.text()
        if not epub_path:
            QMessageBox.warning(self, "错误", "请先选择EPUB文件")
            return
        
        # 准备目标目录
        target_dir = os.path.join("primary fileSet", "epub")
        os.makedirs(target_dir, exist_ok=True)
        
        # 获取文件名并复制文件
        file_name = os.path.splitext(os.path.basename(epub_path))[0]
        target_path = os.path.join(target_dir, f"{file_name}.epub")
        
        try:
            shutil.copyfile(epub_path, target_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"文件复制失败: {str(e)}")
            return

        # 处理章节参数
        chapters = self.chapters_edit.text().strip()
        judge = bool(chapters)
        cypher = []
        
        if judge:
            try:
                cypher = [int(c.strip()) for c in chapters.split(",")]
            except ValueError:
                QMessageBox.warning(self, "错误", "章节格式错误，请用逗号分隔数字")
                return

        try:
            Maindehtml2txt(judge=judge, cypher=cypher, name=file_name)
            QMessageBox.information(self, "成功", "转换完成，结果保存在primary fileSet/txt目录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")

    def select_txt_for_conversion(self):
        default_dir = os.path.join("primary fileSet", "txt")
        path, _ = QFileDialog.getOpenFileName(self, "选择TXT文件", default_dir, "文本文件 (*.txt)")
        if path:
            self.txt_file_edit.setText(os.path.basename(path))

    def convert_txt_to_html(self):
        txt_file = self.txt_file_edit.text()
        output_dir = self.output_dir_edit.text().strip()
        
        if not txt_file:
            QMessageBox.warning(self, "错误", "请先选择TXT文件")
            return
        if not output_dir:
            QMessageBox.warning(self, "错误", "请输入输出目录名")
            return

        try:
            MaindeTxt2Html(input_file=txt_file, output_file=output_dir)
            QMessageBox.information(self, "成功", f"转换完成，结果保存在{output_dir}目录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")

    def create_epub_framework(self):
        renamestr = self.framework_name_edit.text().strip() or "第一个"
        try:
            MaindeGenerateEpubFramework(renamestr=renamestr)
            QMessageBox.information(self, "成功", "框架创建成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建失败: {str(e)}")

    def generate_epub(self):
        pointer = self.source_folder_edit.text().strip() or "第一个"
        renamestr = self.epub_name_edit.text().strip() or "example.epub"
        
        if not renamestr.endswith(".epub"):
            renamestr += ".epub"

        try:
            MaindeGenerateEPUB(pointer=pointer, renamestr=renamestr)
            QMessageBox.information(self, "成功", f"EPUB文件已生成: {renamestr}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")





    def create_menus(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('&文件')
        
        epub_open_action = QAction('打开EPUB', self)
        epub_open_action.triggered.connect(self.open_epub)
        file_menu.addAction(epub_open_action)
        
        text_new_action = QAction('新建文本', self)
        text_new_action.setShortcut("Ctrl+N")
        text_new_action.triggered.connect(self.new_text_file)
        file_menu.addAction(text_new_action)
        
        text_open_action = QAction('打开文本', self)
        text_open_action.setShortcut("Ctrl+O")
        text_open_action.triggered.connect(self.open_text_file)
        file_menu.addAction(text_open_action)
        
        text_save_action = QAction('保存文本', self)
        text_save_action.setShortcut("Ctrl+S")
        text_save_action.triggered.connect(self.save_text_file)
        file_menu.addAction(text_save_action)
        
        text_save_as_action = QAction('另存为', self)
        text_save_as_action.triggered.connect(self.save_as_text_file)
        file_menu.addAction(text_save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('&编辑')
        
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.text_edit.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.text_edit.redo)
        edit_menu.addAction(redo_action)
        
        find_action = QAction("查找", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)

    def open_epub(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开EPUB", "", "EPUB Files (*.epub)")
        if path:
            if self.epub_parser:
                self.epub_parser.temp_dir.cleanup()
                
            try:
                self.epub_parser = EpubParser(path)
                self.setWindowTitle(f"EPUB阅读器 - {self.epub_parser.title}")
                self.update_status(f"已打开EPUB: {os.path.basename(path)}")
                self.update_toc()
                self.tab_widget.setCurrentIndex(0)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开EPUB文件:\n{str(e)}")

    def update_toc(self):
        self.toc_tree.clear()
        for idx, path in enumerate(self.epub_parser.spine_items):
            filename = os.path.basename(path)
            item = QTreeWidgetItem([filename])
            item.setData(0, 100, path)
            self.toc_tree.addTopLevelItem(item)

    def load_content(self, item):
        path = item.data(0, 100)
        self.web_view.setUrl(QUrl.fromLocalFile(path))

    def new_text_file(self):
        if self.check_text_save():
            self.text_edit.clear()
            self.current_text_file = None
            self.update_status("新建文本文件")
            self.text_saved = True
            self.tab_widget.setCurrentIndex(1)

    def open_text_file(self):
        if not self.check_text_save():
            return

        path, _ = QFileDialog.getOpenFileName(self, "打开文本文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if path:
            try:
                with open(path, 'rb') as f:
                    rawdata = f.read(1024)
                    result = chardet.detect(rawdata)
                    encoding = result['encoding'] or 'utf-8'
                
                with open(path, 'r', encoding=encoding, errors='replace') as f:
                    self.text_edit.setText(f.read())
                self.current_text_file = path
                self.update_status(f"已打开: {path}")
                self.text_saved = True
                self.tab_widget.setCurrentIndex(1)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")

    def save_text_file(self):
        if self.current_text_file:
            try:
                with open(self.current_text_file, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.update_status(f"已保存到: {self.current_text_file}")
                self.text_saved = True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
        else:
            self.save_as_text_file()

    def save_as_text_file(self):
        # 修改保存对话框的默认路径
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "另存为", 
            self.default_txt_dir,  # 设置默认路径
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                self.current_text_file = path
                self.update_status(f"已保存到: {path}")
                self.text_saved = True
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    def auto_save(self):
        if self.tab_widget.currentIndex() == 1:  # 仅在文本编辑器标签页生效
            if self.current_text_file and not self.text_saved:
                try:
                    with open(self.current_text_file, 'w', encoding='utf-8') as f:
                        f.write(self.text_edit.toPlainText())
                    self.text_saved = True
                    self.update_status(f"自动保存于 {datetime.datetime.now().strftime('%H:%M:%S')}")
                except Exception as e:
                    QMessageBox.critical(self, "自动保存失败", f"错误信息：{str(e)}")
            elif not self.current_text_file and self.text_edit.toPlainText():
                self.save_text_file()

    def check_text_save(self):
        if not self.text_saved:
            reply = QMessageBox.question(
                self, "未保存的修改",
                "当前文本内容尚未保存，是否要保存？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_text_file()
                return True
            elif reply == QMessageBox.StandardButton.Discard:
                return True
            else:
                return False
        return True

    def mark_unsaved_changes(self):
        self.text_saved = False
        self.update_status("文本已修改")

    def show_find_dialog(self):
        search_text, ok = QInputDialog.getText(
            self, '查找', '输入要查找的内容:')
        if ok and search_text:
            cursor = self.text_edit.textCursor()
            document = self.text_edit.document()
            found = document.find(
                search_text, 
                cursor.position(), 
                QTextDocument.FindFlag.FindCaseSensitively | 
                QTextDocument.FindFlag.FindBackward
            )
            if not found.isNull():
                self.text_edit.setTextCursor(found)
                self.update_status(f"找到: {search_text}")
            else:
                found = document.find(search_text, 0)
                if not found.isNull():
                    self.text_edit.setTextCursor(found)
                    self.update_status(f"找到: {search_text}")
                else:
                    QMessageBox.information(self, '查找', f'未找到: {search_text}')

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def restore_settings(self):
        if self.settings.contains("window/size"):
            self.resize(self.settings.value("window/size"))

    def closeEvent(self, event):
        if self.epub_parser:
            self.epub_parser.temp_dir.cleanup()
        if self.check_text_save():
            self.settings.setValue("window/size", self.size())
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.epub', '.txt')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.epub'):
                self.open_epub_direct(path)
            elif path.lower().endswith('.txt'):
                self.open_text_direct(path)

    def open_epub_direct(self, path):
        if self.epub_parser:
            self.epub_parser.temp_dir.cleanup()
        try:
            self.epub_parser = EpubParser(path)
            self.setWindowTitle(f"EPUB阅读器 - {self.epub_parser.title}")
            self.update_status(f"已打开EPUB: {os.path.basename(path)}")
            self.update_toc()
            self.tab_widget.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开EPUB文件:\n{str(e)}")

    def open_text_direct(self, path):
        if self.check_text_save():
            try:
                with open(path, 'rb') as f:
                    rawdata = f.read(1024)
                    result = chardet.detect(rawdata)
                    encoding = result['encoding'] or 'utf-8'
                
                with open(path, 'r', encoding=encoding, errors='replace') as f:
                    self.text_edit.setText(f.read())
                self.current_text_file = path
                self.update_status(f"已打开: {path}")
                self.text_saved = True
                self.tab_widget.setCurrentIndex(1)
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开文件：{path}\n错误信息：{str(e)}")

if __name__ == '__main__':
    basepath1 = os.path.join('converter','HTML2EPUB','Interim Warehouse')
    basepath2 = os.path.join('primary fileSet','epub')
    dir_list = [basepath1,basepath2]
    for dir in dir_list:
        if not os.path.dirname(dir):
            os.makedirs(dir)
    app = QApplication(sys.argv)
    app.setStyleSheet("""
    QGroupBox {
        font-size: 12pt;
        margin-top: 10px;
    }
    QPushButton {
        min-width: 80px;
        padding: 5px;
    }
""")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



