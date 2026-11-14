from helpers import generate_pages_recursive
import os
import shutil
import sys
def main():

    basePath = '/'
    if len(sys.argv) == 2:
        basePath = sys.argv[1]

    if os.path.exists("./docs"):
        shutil.rmtree("./docs")

    shutil.copytree("./static" , "./docs")

    generate_pages_recursive("./content" , "./template.html", "./docs" , basePath)

if __name__ == "__main__":
    main()