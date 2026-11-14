from helpers import generate_pages_recursive
import os
import shutil
import sys
def main():

    basePath = '/'
    if len(sys.argv) == 2:
        basePath = sys.argv[1]

    if os.path.exists("./public"):
        shutil.rmtree("./public")

    shutil.copytree("./static" , "./public")

    generate_pages_recursive("./content" , "./template.html", "./public" , basePath)

if __name__ == "__main__":
    main()