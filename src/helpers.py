from textnode import TextNode, TextType, BlockType
from htmlnode import LeafNode, ParentNode, HTMLNode
from textnode import text_node_to_html_node
import re
import os

def split_nodes_delimiter(old_nodes: list[TextNode], delimiter: str, text_type: TextType) -> list[TextNode]:

    new_nodes : list[TextNode] = []
    for node in old_nodes:

        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue

        if node.text.count(delimiter) % 2 != 0:
            raise Exception("Invalid Markdown syntax")

        chunks = node.text.split(delimiter)

        for i, chunk in enumerate(chunks):

            if not chunk:
                continue
            if i % 2 == 0:
                new_nodes.append(TextNode(chunk , TextType.TEXT))

            else:
                new_nodes.append(TextNode(chunk , text_type))

    return new_nodes


def extract_markdown_images(text) -> list[tuple]:

    matches = re.findall(r"!\[(.*?)\]\((.*?)\)" , text)

    return matches

def extract_markdown_links(text) -> list[tuple]:

    return re.findall(r"(?<!!)\[(.*?)\]\((.*?)\)", text)

    return matches


def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
    res : list[TextNode] = []


    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            res.append(node)
            continue
        
        images = extract_markdown_images(node.text)

        if not images:
            res.append(node)
            continue

        remaining_texts = node.text

        for alt, url in images:
            markdown_text = f"![{alt}]({url})"

            before, remaining_texts = remaining_texts.split(markdown_text , 1)

            if before:
                res.append(TextNode(before, TextType.TEXT))

            res.append(TextNode(alt , TextType.IMAGE , url))

        if remaining_texts:
            res.append(TextNode(remaining_texts , TextType.TEXT))

    return res


def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:

    res : list[TextNode] = []

    for node in old_nodes:

        if node.text_type != TextType.TEXT:
            res.append(node)
            continue


        links = extract_markdown_links(node.text)
        if not links:
            res.append(node)
            continue

        remaining_text = node.text

        for text, link in links:
            markdown_link = f"[{text}]({link})"

            before, remaining_text = remaining_text.split(markdown_link, 1)

            if before:
                res.append(TextNode(before , TextType.TEXT))

            res.append(TextNode(text , TextType.LINK, link))

        if remaining_text:
            res.append(TextNode(remaining_text , TextType.TEXT))

    return res


def text_to_textnodes(text):

    nodes = [TextNode(text, TextType.TEXT)]

    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)

    return nodes


def markdown_to_blocks(markdown: str) -> list[str] :

    res : list[str] = []

    strings = markdown.split("\n\n")

    for string in strings:
        res.append(string.strip())

    return res



def block_to_block_type(markdown: str) -> BlockType:

    lines = markdown.split("\n")

    if markdown.startswith("```") and markdown.endswith("```"):
        return BlockType.CODE

    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    if all(line.startswith(f"{i}. ") for i, line in enumerate(lines , start=1)):
        return BlockType.ORDERED_LIST

    headings = lines[0].split(" ")
    if markdown.startswith("#") and len(headings) >= 2 and 1 <= len(headings[0]) <= 6 and all(c == '#' for c in headings[0]):
        return BlockType.HEADING

    return BlockType.PARAGRAPH


def text_to_children(text):
    text_nodes = text_to_textnodes(text)

    children = []
    for node in text_nodes:
        html_node = text_node_to_html_node(node)
        children.append(html_node)

    return children

def text_to_code(text):

    lines = text.split("\n")
    content = "\n".join(lines[1:-1])

    child = text_node_to_html_node(TextNode(content, TextType.TEXT))

    code_block = ParentNode("code" , [child])
    return ParentNode("pre" , [code_block])
    
def text_to_quote(text):
    lines = text.split("\n")

    for i in range(len(lines)):
        lines[i] = lines[i].lstrip("> ")

    content = "\n".join(lines)


    return ParentNode("blockquote", text_to_children(content))

def text_to_list(text , type):

    if type == "unordered":
        lines = text.split("\n")

        lines = [line.lstrip("- ") for line in lines]

        list_item = []
        for line in lines:
            html_nodes = text_to_children(line)
            list_item.append(ParentNode("li", html_nodes))

        return ParentNode("ul", list_item)

    if type == 'ordered':
        lines = text.split("\n")

        for i in range(len(lines)):
            lines[i] = lines[i].split(". ")[1]

        list_item = []
        for line in lines:
            html_nodes = text_to_children(line)
            list_item.append(ParentNode("li", html_nodes))

        return ParentNode("ol", list_item)



def markdown_to_html_node(markdown) -> HTMLNode:


    blocks = markdown_to_blocks(markdown)

    children : list[HTMLNode] = []
    for block in blocks:
        block_type = block_to_block_type(block)

        if block_type == BlockType.PARAGRAPH:
            html_node = ParentNode("p", text_to_children(block))
            children.append(html_node)

        elif block_type == BlockType.HEADING:
            level = len(block.split(" " , 1)[0])
            content = block.lstrip("#").strip()
            html_node = ParentNode(f"h{level}" , text_to_children(content))
            children.append(html_node)

        elif block_type == BlockType.CODE:

            html_node = text_to_code(block)
            children.append(html_node)

        elif block_type == BlockType.QUOTE:

            html_node = text_to_quote(block)
            children.append(html_node)

        elif block_type == BlockType.UNORDERED_LIST:
            html_node = text_to_list(block , "unordered")
            children.append(html_node)

        elif block_type == BlockType.ORDERED_LIST:
            html_node = text_to_list(block , "ordered")
            children.append(html_node)

    return ParentNode("div"  , children)


        
def extract_title(markdown):
    lines = markdown.split("\n")

    for line in lines:
        if line.startswith("# "):
            return line.removeprefix("# ").strip()

    raise Exception("No title found")


def generate_page(from_path, template_path, dest_path, basePath):
    print(f"Generating path from {from_path} to {dest_path} using {template_path}")

    markdown_file = None
    template_file = None
    with open(from_path , "r" , encoding="utf-8") as file:
        markdown_file = file.read()

    with open(template_path , "r" , encoding="utf-8") as file:
        template_file = file.read()


    html_string = markdown_to_html_node(markdown_file).to_html()
    title = extract_title(markdown_file)

    template_file = template_file.replace("{{ Title }}", title)

    template_file = template_file.replace("{{ Content }}", html_string)

    template_file = template_file.replace('href="/', f'href="{basePath}"')
    template_file = template_file.replace('src="/', f'src="{basePath}"')

    os.makedirs(os.path.dirname(dest_path) , exist_ok=True)

    with open(dest_path, "w" , encoding="utf-8") as file:
        file.write(template_file)

    

def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, basePath):


        file_items = os.listdir(dir_path_content)


        for item in file_items:
            if item.endswith(".md"):

                markdown_content = None
                template_html = None

                with open(f"{dir_path_content}/{item}" , "r" , encoding='utf-8') as file:
                    markdown_content = file.read()

                with open(template_path , "r" , encoding='utf-8') as file:
                    template_html = file.read()

                title = extract_title(markdown_content)
                html_content = markdown_to_html_node(markdown_content).to_html()

                template_html = template_html.replace("{{ Title }}" , title)
                template_html = template_html.replace("{{ Content }}", html_content)

                template_html = template_html.replace('href="/' ,f'href="{basePath}' )
                template_html = template_html.replace('src="/' ,f'href="{basePath}' )

                os.makedirs(dest_dir_path, exist_ok=True)
                with open(f"{dest_dir_path}/{item.rstrip(".md")}.html", "w" , encoding="utf-8") as file:
                    file.write(template_html)
                    
                
            else:
                generate_pages_recursive(f"{dir_path_content}/{item}", template_path , f"{dest_dir_path}/{item}")


