# -*- coding: utf-8 -*-
"""
PythonPDFPro - 一个面向对象的跨平台全能 PDF 工具（精简实现版）
对标 Adobe Acrobat DC 的核心功能：合并、拆分、提取文本/图片、旋转、加密/解密、基本注释、格式转换等。

说明：
- 本文件包含命令行模式与简易 tkinter GUI（双模式）。
- 使用的主要第三方库：PyMuPDF(fitz), PyPDF2, pdfplumber, reportlab, Pillow, python-docx, openpyxl, tqdm（部分为可选功能）。
- 受篇幅限制，部分高级功能（如完整的 PDF->Word 高保真转换、表单可视化编辑、复杂注释编辑器）在代码中给出可用的实现思路或基础实现，用户可按扩展指南进一步完善。

许可证：MIT
作者：AI 生成（供学习与扩展使用）
"""

import os
import sys
import argparse
import logging
import threading
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger
except Exception:
    PdfReader = PdfWriter = PdfMerger = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except Exception:
    canvas = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    import openpyxl
except Exception:
    openpyxl = None

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# 依赖检查工具函数：列出缺失的第三方包并给出 pip 安装示例命令
def check_dependencies() -> List[str]:
    """检查主要依赖库是否可用，返回缺失库列表，并在日志中打印安装命令示例。"""
    deps = {
        'PyMuPDF (fitz)': bool(fitz),
        'PyPDF2': bool(PdfReader),
        'pdfplumber': bool(pdfplumber),
        'reportlab': bool(canvas),
        'Pillow': bool(Image),
        'python-docx': bool(Document),
        'openpyxl': bool(openpyxl),
        'tqdm': bool(tqdm),
    }
    missing = [name for name, ok in deps.items() if not ok]
    if missing:
        logger.warning('缺少依赖: ' + ", ".join(missing))
        python_exec = sys.executable or 'python'
        # 生成简单的 pip 安装命令（按常用包名）
        install_map = {
            'PyMuPDF (fitz)': 'PyMuPDF',
            'PyPDF2': 'PyPDF2',
            'pdfplumber': 'pdfplumber',
            'reportlab': 'reportlab',
            'Pillow': 'Pillow',
            'python-docx': 'python-docx',
            'openpyxl': 'openpyxl',
            'tqdm': 'tqdm',
        }
        pkgs = [install_map.get(m, m.split()[0]) for m in missing]
        cmd = f"{python_exec} -m pip install " + ' '.join(pkgs)
        logger.info(f"安装命令示例: {cmd}")
    else:
        logger.info('依赖检查通过: 所有主要依赖已安装')
    return missing

import logging
from logging.handlers import RotatingFileHandler

# 配置日志（同时输出到控制台与本地日志文件）
LOG_FILE = Path(__file__).with_name('python_pdf_pro.log')
logger = logging.getLogger('PythonPDFPro')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ---------- 工具类与核心实现（示例实现，面向扩展） ----------
class PdfUtils:
    """通用工具方法（路径检查、进度回调等）"""

    @staticmethod
    def ensure_path(path: str) -> Path:
        """确保路径存在并返回 Path 对象，若目录不存在则创建。"""
        p = Path(path)
        if p.suffix:  # 是文件
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
        else:
            p.mkdir(parents=True, exist_ok=True)
        return p


class PdfEdit:
    """PDF 基础编辑功能：合并、拆分、抽取页、删除页、旋转页面、页面重排等"""

    def __init__(self):
        pass

    def merge_pdfs(self, input_files: List[str], output_path: str, show_progress: bool = True) -> bool:
        """合并多个 PDF 文件到一个输出文件。
        - input_files: 输入 PDF 路径列表
        - output_path: 输出 PDF 路径
        返回 True/False。"""
        try:
            logger.info(f"开始合并 {len(input_files)} 个 PDF -> {output_path}")
            if PdfMerger is None:
                raise RuntimeError("缺少 PyPDF2 库，请先安装 pyPdf2 或 PyPDF2")
            merger = PdfMerger()
            iterable = input_files
            if show_progress and tqdm:
                iterable = tqdm(input_files, desc='Merging PDFs')
            for pdf in iterable:
                merger.append(str(pdf))
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            merger.write(str(out_path))
            merger.close()
            logger.info(f"合并完成：{output_path}")
            return True
        except Exception as e:
            logger.exception(f"合并 PDF 失败: {e}")
            return False

    def split_pdf(self, input_file: str, output_dir: str, ranges: Optional[List[Tuple[int, int]]] = None) -> bool:
        """按页范围拆分 PDF。
        - ranges: 列表，每项为 (start, end)（1-indexed，包含 end）。
        若 ranges 为 None，则按每页拆分为单页 PDF。
        """
        try:
            logger.info(f"开始拆分：{input_file}")
            reader = PdfReader(str(input_file))
            total = len(reader.pages)
            out_dir = PdfUtils.ensure_path(output_dir)
            if ranges:
                for idx, (s, e) in enumerate(ranges, 1):
                    s0 = max(1, s)
                    e0 = min(total, e)
                    writer = PdfWriter()
                    for p in range(s0 - 1, e0):
                        writer.add_page(reader.pages[p])
                    out_file = out_dir / f"{Path(input_file).stem}_part{idx}.pdf"
                    with open(out_file, 'wb') as f:
                        writer.write(f)
                    logger.info(f"拆分生成: {out_file}")
            else:
                for i in range(total):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    out_file = out_dir / f"{Path(input_file).stem}_page_{i+1}.pdf"
                    with open(out_file, 'wb') as f:
                        writer.write(f)
            logger.info("拆分完成")
            return True
        except Exception as e:
            logger.exception(f"拆分 PDF 失败: {e}")
            return False

    def extract_pages(self, input_file: str, pages: List[int], output_file: str) -> bool:
        """提取指定页码（1-indexed）并生成新 PDF。"""
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            total = len(reader.pages)
            for p in pages:
                if 1 <= p <= total:
                    writer.add_page(reader.pages[p - 1])
                else:
                    logger.warning(f"页码 {p} 超出范围：1-{total}")
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'wb') as f:
                writer.write(f)
            logger.info(f"提取页生成：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"提取页失败: {e}")
            return False

    def delete_pages(self, input_file: str, pages_to_delete: List[int], output_file: str) -> bool:
        """删除指定页码并生成新文件。"""
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            total = len(reader.pages)
            to_del = set(pages_to_delete)
            for i in range(1, total + 1):
                if i not in to_del:
                    writer.add_page(reader.pages[i - 1])
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'wb') as f:
                writer.write(f)
            logger.info(f"删除页后生成：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"删除页失败: {e}")
            return False

    def rotate_pages(self, input_file: str, output_file: str, pages: Optional[List[int]] = None, angle: int = 90) -> bool:
        """旋转指定页码或整本（角度 90/180/270）。pages 为 None 表示整本旋转。"""
        try:
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            total = len(reader.pages)
            if pages is None:
                pages_set = set(range(1, total + 1))
            else:
                pages_set = set(pages)
            for i in range(1, total + 1):
                page = reader.pages[i - 1]
                if i in pages_set:
                    page.rotate_clockwise(angle)
                writer.add_page(page)
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'wb') as f:
                writer.write(f)
            logger.info(f"旋转完成：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"旋转失败: {e}")
            return False


class PdfExtract:
    """文本与图片提取相关功能"""

    def extract_text(self, input_file: str, output_txt: Optional[str] = None, pages: Optional[List[int]] = None,
                     preserve_layout: bool = True) -> Optional[str]:
        """从 PDF 提取文本，返回文本并可保存为文件。
        - pages: 1-indexed 列表，None 表示全部页
        - preserve_layout: 若 True 尽量保留排版（使用 pdfplumber）"""
        try:
            logger.info(f"开始提取文本: {input_file}")
            text_parts = []
            if pdfplumber and preserve_layout:
                with pdfplumber.open(input_file) as pdf:
                    total = len(pdf.pages)
                    iter_pages = range(1, total + 1) if pages is None else pages
                    for i in iter_pages:
                        if 1 <= i <= total:
                            page = pdf.pages[i - 1]
                            text_parts.append(page.extract_text() or '')
            elif fitz:
                doc = fitz.open(input_file)
                total = doc.page_count
                iter_pages = range(1, total + 1) if pages is None else pages
                for i in iter_pages:
                    if 1 <= i <= total:
                        p = doc.load_page(i - 1)
                        text_parts.append(p.get_text('text'))
            else:
                raise RuntimeError("缺少 pdfplumber 或 PyMuPDF，无法提取文本")
            text = '\n\n'.join(text_parts)
            if output_txt:
                out = Path(output_txt)
                out.parent.mkdir(parents=True, exist_ok=True)
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"已保存文本到: {output_txt}")
            return text
        except Exception as e:
            logger.exception(f"提取文本失败: {e}")
            return None

    def extract_images(self, input_file: str, output_dir: str, fmt: str = 'png') -> List[str]:
        """提取 PDF 中的所有图片并按原分辨率保存（使用 PyMuPDF）。返回保存路径列表。"""
        saved = []
        try:
            if fitz is None:
                raise RuntimeError("需要安装 PyMuPDF (fitz) 来提取图片")
            doc = fitz.open(input_file)
            out_dir = PdfUtils.ensure_path(output_dir)
            for i in range(doc.page_count):
                page = doc.load_page(i)
                image_list = page.get_images(full=True)
                logger.info(f"第 {i+1} 页，发现图片 {len(image_list)} 个")
                for img_index, img in enumerate(image_list, start=1):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    file_ext = fmt
                    out_file = out_dir / f"{Path(input_file).stem}_p{i+1}_img{img_index}.{file_ext}"
                    try:
                        # 直接将 pix 保存为文件（兼容不同 PyMuPDF 版本）
                        if pix.n - getattr(pix, 'alpha', 0) >= 4:
                            # CMYK 有可能需要转换为 RGB
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        pix.save(str(out_file))
                        saved.append(str(out_file))
                    finally:
                        # 释放 pix
                        try:
                            pix = None
                        except Exception:
                            pass
            logger.info(f"图片提取完成，共保存 {len(saved)} 个文件")
            return saved
        except Exception as e:
            logger.exception(f"提取图片失败: {e}")
            return saved


class PdfEncrypt:
    """加密与解密功能：设置打开密码、设置权限（所有者密码）、移除密码保护等"""

    def encrypt_pdf(self, input_file: str, output_file: str, user_password: str, owner_password: Optional[str] = None,
                    permissions: Optional[dict] = None) -> bool:
        """给 PDF 设置打开密码以及 optional 的 owner 密码/权限限制（基于 PyPDF2）。"""
        try:
            if PdfReader is None:
                raise RuntimeError("需要安装 PyPDF2 来加密/解密 PDF")
            reader = PdfReader(str(input_file))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            # PyPDF2 的 set_encryption 方法：user_pwd, owner_pwd
            if owner_password is None:
                owner_password = user_password
            writer.encrypt(user_pwd=user_password, owner_pwd=owner_password)
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'wb') as f:
                writer.write(f)
            logger.info(f"加密完成：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"加密失败: {e}")
            return False

    def decrypt_pdf(self, input_file: str, output_file: str, password: str) -> bool:
        """已知密码时移除 PDF 密码保护。"""
        try:
            if PdfReader is None:
                raise RuntimeError("需要安装 PyPDF2 来加密/解密 PDF")
            reader = PdfReader(str(input_file))
            if reader.is_encrypted:
                # PyPDF2.decrypt 返回解密状态码：0=失败，1/2=成功（取决于类型）
                dec_res = reader.decrypt(password)
                try:
                    dec_ok = bool(dec_res)
                except Exception:
                    dec_ok = dec_res is not None and dec_res != 0
                if not dec_ok:
                    logger.error("密码错误或无法解密（请确认密码正确）")
                    return False
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'wb') as f:
                writer.write(f)
            logger.info(f"解密并生成：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"解密失败: {e}")
            return False


class PdfConvert:
    """格式转换相关：PDF -> 图片 / DOCX / TXT, 其它 -> PDF（基础实现）"""

    def pdf_to_images(self, input_file: str, output_dir: str, zoom: float = 2.0, fmt: str = 'png') -> List[str]:
        """将 PDF 每页渲染为图片（高质量），返回图像文件列表。"""
        saved = []
        try:
            if fitz is None:
                raise RuntimeError("需要安装 PyMuPDF (fitz) 来渲染 PDF 为图片")
            doc = fitz.open(input_file)
            out_dir = PdfUtils.ensure_path(output_dir)
            for i in range(doc.page_count):
                page = doc.load_page(i)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                out_file = out_dir / f"{Path(input_file).stem}_page_{i+1}.{fmt}"
                pix.save(str(out_file))
                saved.append(str(out_file))
            logger.info(f"PDF->图片 完成，共 {len(saved)} 张")
            return saved
        except Exception as e:
            logger.exception(f"PDF->图片 转换失败: {e}")
            return saved

    def pdf_to_docx(self, input_file: str, output_file: str) -> bool:
        """简易实现：提取文本并写入 docx，保留基础段落结构。高级布局保留需用更复杂工具（如商用软件或 OCR 处理扫描件）。"""
        try:
            text = PdfExtract().extract_text(input_file)
            if text is None:
                raise RuntimeError("提取文本失败，无法生成 DOCX")
            if Document is None:
                raise RuntimeError("缺少 python-docx 库，请安装 python-docx 来导出 Word 文件")
            doc = Document()
            for para in text.split('\n\n'):
                doc.add_paragraph(para)
            out = Path(output_file)
            out.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(out))
            logger.info(f"已生成 Word 文件：{output_file}")
            return True
        except Exception as e:
            logger.exception(f"PDF->DOCX 失败: {e}")
            return False

    # 其它转换（如 Word->PDF、Excel->PDF 等）通常依赖 office 转换工具（libreoffice soffice 或 com 组件），这里只给出提示式实现。


# ---------- 简易 GUI（tkinter）实现 ----------
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except Exception:
    tk = None


class SimpleGUI:
    """基于 tkinter 的简易 GUI，覆盖常用功能入口：打开文件、合并、拆分、提取文本、提取图片、加密/解密。
    设计理念：界面尽量简单直观，适合零基础用户使用；高级功能保留命令行接口。"""

    def __init__(self):
        if tk is None:
            logger.error("tkinter 未找到，GUI 模式不可用")
            raise RuntimeError("tkinter 未找到")
        self.root = tk.Tk()
        self.root.title('PythonPDFPro - 简易 GUI')
        self.root.geometry('800x600')
        self.create_widgets()

    def create_widgets(self):
        frm_top = ttk.Frame(self.root, padding=8)
        frm_top.pack(fill='x')

        ttk.Label(frm_top, text='选择文件:').grid(row=0, column=0, sticky='w')
        self.entry_file = ttk.Entry(frm_top, width=60)
        self.entry_file.grid(row=0, column=1, padx=6)
        ttk.Button(frm_top, text='浏览', command=self.browse_file).grid(row=0, column=2)

        # 功能选择
        frm_mid = ttk.Frame(self.root, padding=8)
        frm_mid.pack(fill='x')
        ttk.Label(frm_mid, text='操作:').grid(row=0, column=0, sticky='w')
        self.combo_action = ttk.Combobox(frm_mid, values=['merge', 'split', 'extract_text', 'extract_images', 'encrypt', 'decrypt'], width=30)
        self.combo_action.grid(row=0, column=1)
        self.combo_action.current(0)

        ttk.Button(frm_mid, text='开始', command=self.run_action).grid(row=0, column=2, padx=6)

        # 参数区域
        frm_params = ttk.Frame(self.root, padding=8)
        frm_params.pack(fill='x')
        ttk.Label(frm_params, text='参数/输出:').grid(row=0, column=0, sticky='w')
        self.entry_params = ttk.Entry(frm_params, width=80)
        self.entry_params.grid(row=0, column=1, padx=6)

        # 日志显示区
        frm_log = ttk.Frame(self.root, padding=8)
        frm_log.pack(fill='both', expand=True)
        self.txt_log = scrolledtext.ScrolledText(frm_log, state='normal')
        self.txt_log.pack(fill='both', expand=True)
        self.log('GUI 启动，准备就绪')

    def log(self, message: str):
        self.txt_log.configure(state='normal')
        self.txt_log.insert('end', message + '\n')
        self.txt_log.see('end')
        self.txt_log.configure(state='disabled')

    def browse_file(self):
        file = filedialog.askopenfilename(filetypes=[('PDF 文件', '*.pdf'), ('所有文件', '*.*')])
        if file:
            self.entry_file.delete(0, 'end')
            self.entry_file.insert(0, file)

    def run_action(self):
        action = self.combo_action.get()
        file = self.entry_file.get()
        params = self.entry_params.get()
        self.log(f'开始执行 {action}，文件: {file}，参数: {params}')
        threading.Thread(target=self._run_action_thread, args=(action, file, params), daemon=True).start()

    def _run_action_thread(self, action, file, params):
        try:
            ed = PdfEdit()
            ex = PdfExtract()
            enc = PdfEncrypt()
            conv = PdfConvert()
            if action == 'merge':
                # params: out=out.pdf;inputs=a.pdf,b.pdf,c.pdf
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                inputs = opts.get('inputs', '')
                out = opts.get('out', 'merged.pdf')
                files = inputs.split(',') if inputs else []
                ok = ed.merge_pdfs(files, out)
                self.log('合并完成' if ok else '合并失败')
            elif action == 'split':
                # params: outdir=out;pages=1-3,5
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                outdir = opts.get('outdir', 'split_out')
                pages = opts.get('pages', '')
                rngs = None
                if pages:
                    # 解析 pages 字符串为 ranges
                    parts = pages.split(',')
                    rngs = []
                    for part in parts:
                        if '-' in part:
                            s, e = part.split('-', 1)
                            rngs.append((int(s), int(e)))
                        else:
                            n = int(part)
                            rngs.append((n, n))
                ok = ed.split_pdf(file, outdir, rngs)
                self.log('拆分完成' if ok else '拆分失败')
            elif action == 'extract_text':
                # params: out=out.txt;pages=1,2,5
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                out = opts.get('out', f"{Path(file).stem}.txt")
                pages = opts.get('pages', '')
                pg = None
                if pages:
                    pg = [int(x) for x in pages.split(',')]
                txt = ex.extract_text(file, out, pages=pg)
                self.log('提取文本完成' if txt is not None else '提取文本失败')
            elif action == 'extract_images':
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                outdir = opts.get('outdir', 'images_out')
                saved = ex.extract_images(file, outdir)
                self.log(f'提取图片完成，共 {len(saved)} 张')
            elif action == 'encrypt':
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                out = opts.get('out', f"{Path(file).stem}_enc.pdf")
                pwd = opts.get('pwd', 'password')
                ok = enc.encrypt_pdf(file, out, pwd)
                self.log('加密完成' if ok else '加密失败')
            elif action == 'decrypt':
                opts = dict([p.split('=', 1) for p in params.split(';') if '=' in p])
                out = opts.get('out', f"{Path(file).stem}_dec.pdf")
                pwd = opts.get('pwd', '')
                ok = enc.decrypt_pdf(file, out, pwd)
                self.log('解密完成' if ok else '解密失败')
            else:
                self.log('不支持的操作')
        except Exception as e:
            logger.exception('GUI 操作失败')
            self.log(f'操作异常: {e}')

    def run(self):
        self.root.mainloop()


# ---------- 命令行接口（argparse） ----------
def build_cli():
    parser = argparse.ArgumentParser(prog='PythonPDFPro', description='PythonPDFPro - 全能 PDF 工具（精简实现）')
    sub = parser.add_subparsers(dest='cmd')

    # 合并
    p_merge = sub.add_parser('merge', help='合并多个 PDF')
    p_merge.add_argument('-i', '--inputs', nargs='+', help='输入 PDF 列表', required=True)
    p_merge.add_argument('-o', '--output', help='输出文件', required=True)

    # 拆分
    p_split = sub.add_parser('split', help='拆分 PDF')
    p_split.add_argument('-i', '--input', help='输入 PDF', required=True)
    p_split.add_argument('-o', '--outdir', help='输出目录', required=True)
    p_split.add_argument('-r', '--ranges', help='页码范围示例: 1-3,5,7-9', default='')

    # 提取文本
    p_text = sub.add_parser('extract_text', help='提取文本')
    p_text.add_argument('-i', '--input', help='输入 PDF', required=True)
    p_text.add_argument('-o', '--output', help='输出 txt 文件', required=False)
    p_text.add_argument('-p', '--pages', help='页码，例如: 1,3,5', default='')

    # 提取图片
    p_img = sub.add_parser('extract_images', help='提取图片')
    p_img.add_argument('-i', '--input', help='输入 PDF', required=True)
    p_img.add_argument('-o', '--outdir', help='图片输出目录', required=True)

    # 加密/解密
    p_enc = sub.add_parser('encrypt', help='加密 PDF')
    p_enc.add_argument('-i', '--input', help='输入 PDF', required=True)
    p_enc.add_argument('-o', '--output', help='输出 PDF', required=True)
    p_enc.add_argument('-p', '--password', help='打开密码', required=True)

    p_dec = sub.add_parser('decrypt', help='解密 PDF')
    p_dec.add_argument('-i', '--input', help='输入 PDF', required=True)
    p_dec.add_argument('-o', '--output', help='输出 PDF', required=True)
    p_dec.add_argument('-p', '--password', help='已知密码', required=True)

    p_gui = sub.add_parser('gui', help='启动 GUI 界面')

    p_check = sub.add_parser('check', help='检查依赖库并给出安装建议')

    return parser


def cli_main(args=None):
    parser = build_cli()
    ns = parser.parse_args(args=args)
    cmd = ns.cmd
    if cmd == 'merge':
        ed = PdfEdit()
        ed.merge_pdfs(ns.inputs, ns.output)
    elif cmd == 'split':
        ed = PdfEdit()
        rngs = None
        if ns.ranges:
            parts = ns.ranges.split(',')
            rngs = []
            for p in parts:
                if '-' in p:
                    s, e = p.split('-', 1)
                    rngs.append((int(s), int(e)))
                else:
                    n = int(p)
                    rngs.append((n, n))
        ed.split_pdf(ns.input, ns.outdir, rngs)
    elif cmd == 'extract_text':
        ex = PdfExtract()
        pages = [int(x) for x in ns.pages.split(',')] if ns.pages else None
        ex.extract_text(ns.input, ns.output, pages=pages)
    elif cmd == 'extract_images':
        ex = PdfExtract()
        ex.extract_images(ns.input, ns.outdir)
    elif cmd == 'encrypt':
        enc = PdfEncrypt()
        enc.encrypt_pdf(ns.input, ns.output, ns.password)
    elif cmd == 'decrypt':
        enc = PdfEncrypt()
        enc.decrypt_pdf(ns.input, ns.output, ns.password)
    elif cmd == 'gui':
        if tk is None:
            logger.error('tkinter 未安装，GUI 模式不可用')
            return
        gui = SimpleGUI()
        gui.run()
    elif cmd == 'check':
        # 运行依赖检查并退出
        missing = check_dependencies()
        if missing:
            logger.warning('存在缺失依赖，参照提示安装后重试')
    else:
        parser.print_help()


if __name__ == '__main__':
    # 入口：支持命令行和 GUI
    cli_main()
