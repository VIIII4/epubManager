import os
import zipfile,shutil
from tempfile import TemporaryDirectory

def create_epub(output_path, new_title,new_autho,cover_image_path=None, output_dir=None):
    # 如果指定了输出路径，则结合输出路径和文件名
    if output_dir:
        output_path = os.path.join(output_dir, output_path)
    
    with TemporaryDirectory() as temp_dir:
        # 创建目录结构
        meta_inf_dir = os.path.join(temp_dir, 'META-INF')
        oebps_dir = os.path.join(temp_dir, 'OEBPS')
        text_dir = os.path.join(oebps_dir, 'text')
        styles_dir = os.path.join(oebps_dir, 'styles')
        images_dir = os.path.join(oebps_dir, 'images')
        os.makedirs(meta_inf_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)
        os.makedirs(styles_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)

        # 创建mimetype文件（必须无压缩）
        with open(os.path.join(temp_dir, 'mimetype'), 'w', encoding='utf-8') as f:
            f.write('application/epub+zip')

        # 创建container.xml
        container_content = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        with open(os.path.join(meta_inf_dir, 'container.xml'), 'w', encoding='utf-8') as f:
            f.write(container_content)

        # 创建package.opf文件
        opf_manifest = []
        opf_spine = []
        
        # 核心文件清单
        files_to_add = [
            ('nav.xhtml', 'application/xhtml+xml', 'nav'),
            ('styles/style.css', 'text/css', None),
            ('text/cover.xhtml', 'application/xhtml+xml', None)
        ]
        
        # 如果提供封面图片
        if cover_image_path and os.path.exists(cover_image_path):
            cover_dest = os.path.join(images_dir, 'cover.jpg')
            shutil.copy(cover_image_path, cover_dest)
            files_to_add.append(('images/cover.jpg', 'image/jpeg', 'cover-image'))
        
        # 生成manifest内容
        opf_manifest = '\n'.join(
            f'<item id="{item_id}" href="{path}" media-type="{mtype}"{" properties=\""+item_id+"\"" if item_id else ""}/>'
            for path, mtype, item_id in files_to_add
        )

        opf_content = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uid">urn:uuid:12345678-1234-5678-1234-567812345678</dc:identifier>
        <dc:title>{new_title}</dc:title>
        <dc:creator>{new_autho}</dc:creator>
        <dc:language>zh-CN</dc:language>
        <meta property="dcterms:modified">2024-01-01T00:00:00Z</meta>
    </metadata>
    <manifest>
        {opf_manifest}
        <item id="chapter1" href="text/chapter1.xhtml" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="cover"/>
        <itemref idref="nav"/>
        <itemref idref="chapter1"/>
    </spine>
    <guide>
        <reference type="cover" title="封面" href="text/cover.xhtml"/>
    </guide>
</package>'''
        with open(os.path.join(oebps_dir, 'package.opf'), 'w', encoding='utf-8') as f:
            f.write(opf_content)

        # 创建导航文件
        nav_content = '''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目录</title></head>
<body>
    <nav epub:type="toc">
        <h1>目录</h1>
        <ol>
            <li><a href="text/cover.xhtml">封面</a></li>
            <li><a href="text/chapter1.xhtml">第一章</a></li>
        </ol>
    </nav>
</body>
</html>'''
        with open(os.path.join(oebps_dir, 'nav.xhtml'), 'w', encoding='utf-8') as f:
            f.write(nav_content)

        # 创建默认样式表
        css_content = '''body { font-family: serif; margin: 1em; }
h1 { font-size: 2em; text-align: center; }
.chapter p { text-indent: 2em; }'''
        with open(os.path.join(styles_dir, 'style.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)

        # 创建空白封面页
        cover_content = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>封面</title>
<link rel="stylesheet" href="../styles/style.css"/></head>
<body>
    <section class="cover">
        <h1>{new_title}</h1>
        <p>{new_autho}</p>
    </section>
</body>
</html>'''
        with open(os.path.join(text_dir, 'cover.xhtml'), 'w', encoding='utf-8') as f:
            f.write(cover_content)

        # 创建示例章节
        chapter_content = '''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>第一章</title>
<link rel="stylesheet" href="../styles/style.css"/></head>
<body>
    <section class="chapter">
        <h1>第一章</h1>
        <p>这是第一个段落。</p>
        <ul>
            <li>列表项1</li>
            <li>列表项2</li>
        </ul>
    </section>
</body>
</html>'''
        with open(os.path.join(text_dir, 'chapter1.xhtml'), 'w', encoding='utf-8') as f:
            f.write(chapter_content)

        # 打包EPUB文件
        with zipfile.ZipFile(output_path, 'w') as epub:
            # 首先添加mimetype（必须无压缩）
            epub.write(
                os.path.join(temp_dir, 'mimetype'),
                'mimetype',
                compress_type=zipfile.ZIP_STORED
            )
            
            # 添加其他文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == 'mimetype':
                        continue
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, temp_dir)
                    epub.write(full_path, arcname)


def extract_epub(epub_path, rename_string):
    # 获取EPUB文件的绝对路径及其所在目录
    epub_abs_path = os.path.abspath(epub_path)
    epub_dir = os.path.dirname(epub_abs_path)
    
    # 构建目标文件夹路径
    target_dir = os.path.join(epub_dir, rename_string)
    
    # 确保目标文件夹存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 解压EPUB文件到目标文件夹
    with zipfile.ZipFile(epub_abs_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    
    # 返回解压后的文件夹路径
    return target_dir



def MaindeGenerateEpubFramework(renamestr=None):
    basepath1 = os.path.join('converter','HTML2EPUB','Interim Warehouse')
    if not os.path.exists(basepath1):
        os.makedirs(basepath1)
    if renamestr == "" or renamestr is None:
        renamestr = "第一个"
    output_path = os.path.join('converter', 'HTML2EPUB', 'Interim Warehouse')
    epub_path = os.path.join('converter', 'HTML2EPUB', 'Interim Warehouse', 'example.epub')
    create_epub('example.epub', "新标题", "新作者", output_dir=output_path)
    extract_epub(epub_path, str(renamestr))
    


if __name__ == '__main__':
    #epub_path = os.path.join('converter', 'HTML2EPUB', 'Interim Warehouse', 'example.epub')
    # 示例调用，指定输出路径
    # create_epub('example.epub', "新标题", "新作者", output_dir=r'converter\HTML2EPUB\Interim Warehouse')
    #extract_epub(epub_path, "第三个")
    MaindeGenerateEpubFramework()
    # extract_epub(r'D:\python\epubManager\converter\HTML2EPUB\Interim Warehouse\example.epub', "第三个")