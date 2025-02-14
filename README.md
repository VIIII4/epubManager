# EPUB 文档管理工具

## 项目简介
~~本工具提供 EPUB 文档的全生命周期管理，支持格式转换、内容编辑、元数据修改等功能，采用 PyQt6 实现图形化界面。~~
实际上是实时编辑txt,弄好一章放入先前建好的书框里，觉得写够了就执行成书命令。不过支持预览 EPUB 文档阅读
该工具目前仅支持 Windows 系统


## 主要功能
### 转换工具
- 📘 EPUB → TXT 转换（支持章节选择）
- 📄 TXT → HTML 转换（自动生成结构化文档）
- 🖥️ HTML → EPUB 框架生成

### EPUB 管理
- 🆕 创建 EPUB 框架模板
- ✏️ 动态编辑章节内容
- 🗑️ 删除指定章节/封面
- 📝 修改元数据（标题/作者）
- 🔍 预览 EPUB 内容

## 环境要求
```bash
pip install -r requirements.txt

打包成exe

pyinstaller --onefile --noconsole --name "EpubManager" --icon="tupian.ico" `
--hidden-import PyQt6.QtWebEngineWidgets `
--exclude-module PyQt6.QtQml `
--exclude-module PyQt6.QtQuick `
--clean `
app.py


epubManager/
├── converter/               # 格式转换模块
│   ├── HTML2EPUB/           # HTML转EPUB核心逻辑
│   └── txt2html.py          # 文本格式化工具
├── erase.py                 # 元数据/章节删除功能
├── app.py                   # 主界面GUI实现
└── Interim Warehouse/       # 临时文件存储区


# 后续优化计划
1.实现daemon模式，后台运行
2.添加API接口
3.实现多线程处理，提高效率

else
本内容按"=== 标题 ==="格式分割为多个带标题的章节。
如果文本内并不包含"=== 标题 ==="格式，则文本文件的名称（除后缀）当“标题”
UPX（Ultimate Packer for eXecutables）是一款用于压缩可执行文件的工具，使用它可以减小 PyInstaller 打包后文件的大小