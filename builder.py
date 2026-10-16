import os
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(["pages", "templates"]),
    autoescape=select_autoescape(["html", "xml"])
)

PAGES_DIR = "pages"
PUBLIC_DIR = ".public"


def build_file(fname: str):
    template = env.get_template(fname)
    rendered: str = template.render()
    print(rendered)
    return rendered


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
            src_file = file.replace("\\", "/").replace("//", "/")
            src_path = root_dest + '/' + src_file
            dest_path = (PUBLIC_DIR + '/' + root_dest + '/' + file).replace("\\", "/").replace("//", "/")
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            print("Building", src_file, "at", src_path)
            built_file: str = build_file(src_path)

            print(dest_path)

            with open(dest_path, 'w') as f:
                f.write(built_file)


if __name__ == "__main__":
    build()
