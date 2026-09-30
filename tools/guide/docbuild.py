#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docbuild —— 《pcaptool 完全教程》的排版工具箱
================================================
所有章节脚本（pa_front.py、pb_basics.py ...）共用同一个 docbuild 里的文档对象，
调用 h1 / h2 / para / code / bullet / note / qa 这些函数往文档里写内容。
最后用 save() 一次性保存成 .docx 文件。
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()

# 正文用微软雅黑，中文看着舒服。
normal = doc.styles['Normal']
normal.font.name = 'Microsoft YaHei'
normal.font.size = Pt(11)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')


def cover(title, subtitle, meta):
    """封面页：大标题 + 副标题 + 说明文字（都居中）。"""
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(30)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(subtitle)
    r2.font.size = Pt(14)
    for _ in range(5):
        doc.add_paragraph()
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run(meta)
    r3.font.size = Pt(11)
    r3.font.color.rgb = RGBColor(0x60, 0x60, 0x60)


def h1(text, new_page=True):
    """一级标题（章）。默认从新的一页开始。"""
    if new_page:
        doc.add_page_break()
    doc.add_heading(text, level=1)


def h2(text):
    """二级标题（节）。"""
    doc.add_heading(text, level=2)


def h3(text):
    """三级标题（小节）。"""
    doc.add_heading(text, level=3)


def para(text):
    """正文段落。一段文字对应文档里的一段。"""
    doc.add_paragraph(text)


def bullet(text):
    """圆点列表里的一项。"""
    doc.add_paragraph(text, style='List Bullet')


def code(text):
    """代码 / 命令 / 程序输出块：用等宽字体，前后留点空隙。"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = 'Consolas'
    r.font.size = Pt(9.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    return p


def note(text):
    """灰色斜体小提示，用来放"小坑"和"冷知识"。"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = True
    r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
    return p


def qa(q, a):
    """问答对（FAQ 用）：问题加粗，答案普通。"""
    p = doc.add_paragraph()
    r = p.add_run('Q：' + q)
    r.bold = True
    doc.add_paragraph('A：' + a)


def save(path):
    """保存文档到指定路径（自动建目录）。"""
    import os
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    doc.save(path)
    print('已生成', path)
