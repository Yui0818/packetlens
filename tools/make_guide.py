#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《packetlens 完全教程（小白版）》
====================================
运行：python3 tools/make_guide.py
输出：docs/packetlens完全教程.docx

各章节的内容在 tools/guide/ 文件夹下的 pa_*.py ~ pm_*.py 里，
本脚本按顺序导入它们（导入即执行，把内容拼进同一个文档），最后保存。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'guide'))

# 导入顺序 = 文档里章节的顺序
import docbuild

# 完全教程的样子：墨绿标题、封面留白多一点、页码写成「第 N 页」
docbuild.configure(h1='1B4D3E', h2='2C7059', h3='46756A',
                   cover_top=7, cover_mid=4, footer='cn', title_size=32)

import pa_front      # 封面 · 前言
import pb_basics     # 第 1 章  电脑与编程的最基础概念
import pc_network    # 第 2 章  网络基础
import pd_project    # 第 3 章  项目全貌
import pe_code1      # 第 4 章（上）main.c 逐行
import pf_code2      # 第 4 章（中）parse_packet
import pg_code3      # 第 4 章（下·一）print_packet 与统计
import ph_code4      # 第 4 章（下·二）过滤器与 main
import pi_files      # 第 5 章  其余文件详解
import pj_usage      # 第 6 章  使用手册 + 急救箱
import pk_github     # 第 7 章  GitHub 界面完全图解
import pl_faq        # 第 8 章  FAQ
import pm_next       # 第 9 章  下一步
import po_design     # 第 10 章 设计决策集
import pn_appendix   # 附录 A~D  速查手册
import pp_appendix2  # 附录 E~F  练习 25 题 + 面试 25 问

if __name__ == '__main__':
    out = os.path.abspath(os.path.join(HERE, '..', 'docs', 'packetlens完全教程.docx'))
    docbuild.save(out, title='PacketLens 完全教程', created='2026-09-30 21:28')
