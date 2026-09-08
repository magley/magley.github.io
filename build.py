import os
import shlex
import shutil


PAGES_DIR = "pages"
PUBLIC_DIR = ".public"


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

        cmd = contents[L + 2:R].strip()
        cmd, variables = parse_content(cmd, variables)
        parts = shlex.split(cmd)

        if len(parts) == 0:
            pass
        else:
            if parts[0] == 'import':
                if len(parts) == 1:
                    print(f"Don't know what to import: {cmd}")
                else:
                    template_path = parts[1]
                    variables |= parse_variables(parts[2:])
                    contents2 += build_file(template_path, variables)
            elif parts[0] == 'var':
                if len(parts) == 1:
                    print(f"Don't know what variable to substitute: {cmd}")
                else:  
                    var_name = parts[1]
                    default = parts[2] if len(parts) >= 3 else ''
                    contents2 += variables.get(var_name, default)
            elif parts[0] == 'define':
                if len(parts) == 2:
                    print(f"Don't know name or value of variable: {cmd}")
                else:
                    var_name = parts[1]
                    var_value = parts[2]
                    variables[var_name] = var_value
                    print(var_name, " ", var_value)

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