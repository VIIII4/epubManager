import zipfile,os
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
import shutil

class EpubToTextConverter:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.temp_dir = Path(f"temp_epub_{id(self)}")
        self.opf_path = None
        self.html_files = []

    def _unzip_epub(self):
        """解压 EPUB 文件到临时目录"""
        self.temp_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(self.epub_path, 'r') as z:
            z.extractall(self.temp_dir)
    
    def _parse_container(self):
        """解析 container.xml 获取 OPF 路径"""
        container_path = self.temp_dir / "META-INF" / "container.xml"
        tree = ET.parse(container_path)
        root = tree.getroot()
        ns = {'n': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        self.opf_path = root.find('.//n:rootfile', ns).attrib['full-path']
    
    def _parse_opf(self):
        """解析 OPF 文件并按阅读顺序获取带标题的 HTML 文件"""
        opf_fullpath = self.temp_dir / self.opf_path
        opf_dir = opf_fullpath.parent
        
        tree = ET.parse(opf_fullpath)
        root = tree.getroot()
        ns = {'pkg': 'http://www.idpf.org/2007/opf'}
        
        # 解析 manifest
        manifest = root.find('pkg:manifest', ns)
        items = {}
        for item in manifest.findall('pkg:item', ns):
            items[item.attrib['id']] = {
                'href': opf_dir / item.attrib['href'],
                'type': item.attrib['media-type']
            }
        
        # 解析 spine 获取阅读顺序
        spine = root.find('pkg:spine', ns)
        for itemref in spine.findall('pkg:itemref', ns):
            item_id = itemref.attrib['idref']
            item = items.get(item_id)
            if item and item['type'] == 'application/xhtml+xml':
                self._add_html_file(item['href'])
    
    def _add_html_file(self, file_path):
        """解析单个 HTML 文件并记录标题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                title = soup.title.string.strip() if soup.title else ''
                self.html_files.append({
                    'path': file_path,
                    'title': title
                })
        except Exception as e:
            print(f"解析文件 {file_path} 失败: {e}")

    def _html_to_text(self, html_path):
        """将 HTML 转换为格式化文本"""
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml-xml')
            
            # 移除不需要的元素
            for elem in soup(['style', 'script', 'head', 'meta', 'link']):
                elem.decompose()
            
            # 处理特殊格式
            self._process_lists(soup)
            self._process_headings(soup)
            
            # 获取文本内容
            text = soup.get_text(separator='\n', strip=True)
            return self._clean_whitespace(text)
    
    def _process_lists(self, soup):
        """处理列表格式"""
        for ul in soup.find_all('ul'):
            ul.insert_before('\n')
            for li in ul.find_all('li'):
                li.insert_before('• ')
                li.append('\n')
            ul.unwrap()
    
    def _process_headings(self, soup):
        """为标题添加换行"""
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            h.insert_before('\n\n')
            h.append('\n')
    
    def _clean_whitespace(self, text):
        """清理空白字符"""
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
        return '\n\n'.join(lines)
    
    def convert(self, target_titles=None, output_path="output.txt"):
        """执行转换主流程"""
        # 初始化处理
        self._unzip_epub()
        self._parse_container()
        self._parse_opf()
        
        # 筛选目标文件
        target_set = set(target_titles) if target_titles else None
        matched = [
            f for f in self.html_files
            if not target_set or f['title'] in target_set
        ]
        
        if not matched:
            print("未找到匹配的章节")
            return
        
        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in matched:
                text = self._html_to_text(item['path'])
                f.write(f"=== {item['title']} ===\n\n")
                f.write(text)
                f.write('\n\n\n')
        
        # 清理临时文件
        shutil.rmtree(self.temp_dir)
        print(f"转换完成: 共转换 {len(matched)} 个章节")


def judge_file_name(file_name):
    root, ext = os.path.splitext(file_name)
    if ext:
        return 
    else:
        return 


def Maindehtml2txt(judge,cypher,name):

    root, ext = os.path.splitext(name)
    if ext:
        epub_path = os.path.join('primary fileSet','epub',str(name))
        outpath = os.path.join('primary fileSet','txt',str(name))
    else:
        epub_path = os.path.join('primary fileSet','epub',str(name+".epub"))
        outpath = os.path.join('primary fileSet','txt',str(name+'.txt'))

    converter = EpubToTextConverter(epub_path)
    if judge == True:
        if type(cypher) == list:     
            # 转换特定章节
            converter.convert(
                target_titles=cypher,
                output_path=outpath
            )    
        elif type(cypher) == str:
            converter.convert(
                target_titles=[cypher],
                output_path=outpath
            )
        
        
    else:# 转换全部章节
        converter.convert(output_path=outpath)

        





# 使用示例
if __name__ == "__main__":
    # # 修改为从命令行参数获取EPUB文件路径
    # epub_path = r"D:\python\epubManager\converter\your_book.epub"
    # epub_path = os.path.join('output.epub')
    # converter = EpubToTextConverter(epub_path)
    
    # # 转换特定章节
    # converter.convert(
    #     target_titles=["第一章"],
    #     output_path="selected_chapters.txt"
    # )
    
    # # 转换全部章节
    # converter.convert(output_path=os.path.join('output.txt'))
    Maindehtml2txt(True,['第一章'],'test')