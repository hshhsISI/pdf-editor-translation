# -*- coding: utf-8 -*-
"""
配置文件：PythonPDFPro 的依赖与安装说明、使用说明的简要摘要。
可按需扩展为 JSON/YAML 配置。
"""

DEPENDENCIES = {
    'base': [
        'PyMuPDF',  # fitz，用于文本/图片/渲染
        'PyPDF2',
        'pdfplumber',
        'reportlab',
        'Pillow',
        'tqdm',
    ],
    'optional': [
        'python-docx',
        'openpyxl',
        'pytesseract',
    ]
}

INSTALL_CMD_TEMPLATE = "{python} -m pip install {packages}"

README_SHORT = '''
安装示例（使用指定 Python 可执行文件）：
Windows:
D:/Python3.11/python.exe -m pip install PyMuPDF PyPDF2 pdfplumber reportlab Pillow tqdm python-docx openpyxl

Mac/Linux:
python3 -m pip install PyMuPDF PyPDF2 pdfplumber reportlab Pillow tqdm python-docx openpyxl

说明：
- 若需 OCR 支持，请安装 tesseract 引擎与 pytesseract Python 包。
- 若需将 Word/Excel 转为 PDF，可使用 libreoffice 的命令行转换（soffice）。
'''

PLATFORM_NOTES = {
    'Windows': '确保已安装 Microsoft Visual C++ Build Tools（若遇到编译问题），若要使用打印功能请确保系统已配置默认打印机。',
    'Mac': '可能需要安装 Xcode Command Line Tools。若使用 GUI，请确保系统允许应用显示。',
    'Linux': '可能需要安装 libmupdf、poppler 等系统依赖，或使用 pip wheel 安装 PyMuPDF。'
}

LICENSE = 'MIT'
