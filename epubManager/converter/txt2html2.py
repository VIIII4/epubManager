import os
import re

class Txt2Html:
    def __init__(self, input_file, output_dir,filename):
        self.input_file = input_file
        self.output_dir = output_dir
        self.filename = filename
        os.makedirs(output_dir, exist_ok=True)

    def parse(self):
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = self._split_sections(content)
        for title, body in sections:
            html_content = self._generate_html(title, body)
            self._write_file(title, html_content)

    def _split_sections(self, content):
        pattern = r'^=== (.*?) ===$'
        sections = []
        current_title = None
        current_body = []
        
        for line in content.splitlines():
            match = re.match(pattern, line)
            if match:
                if current_title is not None:
                    sections.append((current_title, current_body))
                current_title = match.group(1)
                current_body = []
            else:
                current_body.append(line)
        
        if current_title is not None:
            sections.append((current_title, current_body))
    
        if not sections:
            title = os.path.splitext(os.path.basename(self.filename))[0]
            return [(title, content.splitlines())]
        return sections

    def _generate_html(self, title, body):
        filtered = [line.rstrip('\n') for line in body]
        processed = filtered[1:] if filtered else []
        
        elements = []
        in_list = False
        paragraph = []
        current_paragraph = ""    
        for line in processed:
            if line.startswith('•'):
                if paragraph:
                    elements.append(f'<p>{"".join(paragraph)}</p>')
                    paragraph = []
                if not in_list:
                    elements.append('<ul>')
                    in_list = True
                elements.append(f'    <li>{line[1:].strip()}</li>')
                
            else:
                if in_list:
                    elements.append('</ul>')
                    in_list = False
                
                # 每行文本单独生成段落
                if line:
                    elements.append(f'<p>{line}</p>')
                elif line == '':
                    elements.append(f'<p></p>')
        



        if in_list:
            elements.append('</ul>')
        if paragraph:
            elements.append(f'<p>{"".join(paragraph)}</p>')
        
        return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{title}</title>
<link rel="stylesheet" href="../styles/style.css"/></head>
<body>
    <section class="chapter">
        <h1>{title}</h1>
        {"\n        ".join(elements)}
    </section>
</body>
</html>'''

    def _write_file(self, title, content):
        filename = f"{title.replace(' ', '_')}.xhtml"
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

def MaindeTxt2Html(input_file, output_file):
    inp = os.path.join('primary fileSet','txt',str(input_file))
    o = os.path.join('converter','HTML2EPUB','Interim Warehouse',str(output_file),'OEBPS','text')
    converter = Txt2Html(inp,o,str(input_file))
    converter.parse()


# 使用示例
if __name__ == "__main__":
    MaindeTxt2Html("某库中的类.txt", "第一个")