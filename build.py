import os
import shlex
import shutil
from html.parser import HTMLParser
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


PAGES_DIR = "pages"
PUBLIC_DIR = ".public"


def get_define_var(file_path: str, name: str, default: str, variables: dict) -> str:
    # Slow, and extracted code from parse_content

    contents = ''
    with open(file_path) as f: contents = f.read()

 
    L: int = 0
    R: int = 0

    while True:
        oldL = L
        L = contents.find("{{", L)
        if L == -1:
            break

        R = find_next_closing_brace(contents, L)
        if R == -1:
            L = R + 2
            continue

        cmd = contents[L + 2:R].strip()
        cmd, variables = parse_content(cmd, variables)
        parts = shlex.split(cmd)

        if len(parts) == 0:
            pass
        else:
            if parts[0] == 'define':
                if len(parts) <= 2:
                    print(f"Could not get define name or value: {cmd}")
                else:
                    var_name = parts[1]
                    var_value = parts[2]
                    if var_name == name:
                        return var_value
        L = R + 2
    return default


class HTMLMetaTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
    
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            name = None
            content = None
            for attr in attrs:
                if attr[0] == 'name': name = attr[1]
                elif attr[0] == 'content': content = attr[1]

            if name is not None and content is not None:
                self.meta[name] = content


def get_meta_tag(file_path: str, meta: str, default: str) -> str:
    # Slow

    text = ''
    with open(file_path) as f: text = f.read()

    parser = HTMLMetaTagParser()
    parser.feed(text)

    return parser.meta.get(meta, default)


def find_next_closing_brace(text: str, start_pos: int) -> int:
    # This is like find() but it respects nested {{ }}.
    # text[start_pos] should be "{{".

    i = start_pos
    cnt = 0
    while i < len(text):
        if text[i:i+2] == '{{':
            cnt += 1
            i += 1
        elif text[i:i+2] == '}}':
            cnt -= 1
            if cnt == 0:
                return i
            i += 1
        else:
            pass
        i += 1
    
    return -1


def parse_variables(variables: list[str]) -> dict:
    d = {}
    for v in variables:
        parts = v.split("=")
        if len(parts) != 2:
            print("Unknown variable definition:", v)
        else:
            d[parts[0]] = parts[1]
    return d


def parse_content(contents: str, variables: dict = {}) -> (str, dict):
    L: int = 0
    R: int = 0
    contents2: str = ''

    while True:
        oldL = L
        L = contents.find("{{", L)
        if L == -1:
            contents2 += contents[oldL:]
            break

        contents2 += contents[oldL:L]

        R = find_next_closing_brace(contents, L)
        if R == -1:
            L = R + 2
            continue

        cmd: str = contents[L + 2:R].strip()
        cmd, variables = parse_content(cmd, variables)
        parts = shlex.split(cmd)

        if len(parts) == 0:
            pass
        else:
            if parts[0] == 'import': # Copy-paste other html file, building it entirely
                if len(parts) == 1:
                    print(f"Don't know what to import: {cmd}")
                else:
                    template_path = parts[1]
                    variables_plus_arguments = variables | parse_variables(parts[2:])
                    contents2 += build_file(template_path, variables_plus_arguments)
            elif parts[0] == 'var': # Get variable, from `define` or as argument from `import`
                if len(parts) == 1:
                    print(f"Don't know what variable to substitute: {cmd}")
                else:  
                    var_name = parts[1]
                    default = parts[2] if len(parts) >= 3 else ''
                    contents2 += variables.get(var_name, default)
            elif parts[0] == 'define': # Define variable, usable from that point to below
                if len(parts) <= 2:
                    print(f"Don't know name or value of variable: {cmd}")
                else:
                    var_name = parts[1]
                    var_value = parts[2]
                    variables[var_name] = var_value
            elif parts[0] == 'meta': # Get <meta> from specified BUILT html file 
                if len(parts) <= 2:
                    print(f"Don't know which .html file to use or meta tag: {cmd}")
                else:
                    html_file_path = PUBLIC_DIR + "/" + parts[1]
                    meta_tag = parts[2]
                    default = parts[3] if len(parts) >= 4 else ''
                    contents2 += get_meta_tag(html_file_path, meta_tag, default)
            elif parts[0] == "getdefine": # Get value of `define` from specified UNBUILT html file
                if len(parts) <= 2:
                    print(f"Don't know which .html file to use or definition var: {cmd}")
                else:
                    html_file_path = PAGES_DIR + "/" + parts[1]
                    meta_tag = parts[2]
                    default = parts[3] if len(parts) >= 4 else ''
                    contents2 += get_define_var(html_file_path, meta_tag, default, variables)
            elif parts[0] == "code": # Syntax highlighting
                if len(parts) <= 3:
                    print(f"Don't know which language to use or what the code is: {cmd}")
                else:
                    lang = parts[1]
                    code: str = cmd.split(None, 2)[2]

                    contents2 += highlight(code, get_lexer_by_name(lang), HtmlFormatter())

        L = R + 2
    return contents2, variables


def build_file(path: str, variables: dict = {}) -> str:
    contents: str = ''
    with open(path) as f:
        contents = f.read()
    result, _ = parse_content(contents, variables)
    return result
    

def build():    
    try:
        shutil.rmtree(PUBLIC_DIR)
    except:
        pass
    os.mkdir(PUBLIC_DIR)

    shutil.copytree("./assets/", PUBLIC_DIR + "/assets/", dirs_exist_ok=True)

    for root, dirs, files in os.walk(PAGES_DIR):
        root_dest = root # Root without PAGES_DIR, i.e. path of `files` relative to PAGES_DIR
        if root_dest.startswith(PAGES_DIR):
            root_dest = root_dest[len(PAGES_DIR) + 1:]
        
        for file in files:
            src_path = root + '/' + file.replace("\\", "/").replace("//", "/")
            dest_path = (PUBLIC_DIR + '/' + root_dest + '/' + file).replace("\\", "/").replace("//", "/")
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            built_file: str = build_file(src_path, {})

            with open(dest_path, 'w') as f:
                print("Building", dest_path)
                f.write(built_file)


if __name__ == '__main__':
    build()