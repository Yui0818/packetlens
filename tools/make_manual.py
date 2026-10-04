#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《packetlens 逐行手册》
==========================
运行：python3 tools/make_manual.py
输出：docs/packetlens逐行手册.docx

组成：
  - tools/manual/mz_intro.py       封面 + 手册使用说明
  - tools/manual/ma_ops.py         第一部分：操作手册（每一步）
  - tools/manual/mb_lines_main_*.py  第二部分：main.c 每一行的解释（按行号索引）
  - tools/manual/mc_lines_sample.py  第三部分：make_sample.py 每一行的解释
  - tools/manual/md_lines_others.py  第四~八部分：Makefile / push.bat / .gitignore / LICENSE / README

本脚本会「现场读取」源文件，把每个源文件的行和对应的解释配对排版——
所以手册里出现的行号永远是文件的真实行号。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, 'guide'))    # 复用完全教程的排版工具箱
sys.path.insert(0, os.path.join(HERE, 'manual'))

import docbuild
from docbuild import cover, h1, h2, h3, para, bullet, code, note, qa, save

# 各部分的内容模块
import mz_intro                                   # import 即写入（封面与说明）
import ma_ops                                     # import 即写入（操作手册）
from mb_lines_main_1 import EXPLAINS as E_MAIN_1
from mb_lines_main_2 import EXPLAINS as E_MAIN_2
from mb_lines_main_3 import EXPLAINS as E_MAIN_3
from mc_lines_sample import EXPLAINS as E_SAMPLE
import md_lines_others as others

MAIN_EXPLAINS = {}
MAIN_EXPLAINS.update(E_MAIN_1)
MAIN_EXPLAINS.update(E_MAIN_2)
MAIN_EXPLAINS.update(E_MAIN_3)

# main.c 的分区目录（行号 → 小节标题），也是手册里的「地图」
MAIN_BREAKS = {
    1:   '① 文件头：版本史记与程序说明（第 1~19 行）',
    21:  '② include：借用四个工具箱（第 21~26 行）',
    32:  '③ rd16：手工拼 2 个字节（第 32~38 行）',
    40:  '④ rd32：手工拼 4 个字节（第 40~44 行）',
    46:  '⑤ print_mac / print_ipv4_addr：地址翻译官（第 46~56 行）',
    58:  '⑥ ip_to_key / print_ip_from_key：给 IP 建档案号（第 58~70 行）',
    72:  '⑦ proto_name / ethertype_name：数字翻译成名字（第 72~90 行）',
    92:  '⑧ print_tcp_flags：一个字节拆成八个开关（第 92~105 行）',
    107: '⑨ PacketInfo 档案袋（第 107~137 行）',
    139: '⑩ parse_packet：拆包核心（第 139~231 行）',
    233: '⑪ print_packet：把档案袋打印成人话（第 233~282 行）',
    284: '⑫ 统计系统·计数器表与全局变量（第 284~318 行）',
    320: '⑬ counter_add / counter_sort（第 320~353 行）',
    355: '⑭ stats_update：把包记进账本（第 355~380 行）',
    382: '⑮ emit_stats：输出统计报告（第 382~421 行）',
    423: '⑯ write_report：第一次写文件（第 423~441 行）',
    443: '⑰ 过滤器·Filter 与参数解析（第 443~504 行）',
    506: '⑱ filter_match：三条军规（第 506~523 行）',
    525: '⑲ handle_packet：两种模式共用的流水线（第 525~553 行）',
    555: '⑳ main：主函数逐行（第 555~704 行）',
}


def line_by_line(relpath, explains, title, breaks=None):
    """把「源文件的每一行」和「对应的解释」配对排进文档。"""
    h1(title)
    para('【读法】每个条目 = 源文件里的一行：先给行号（和电脑上源文件的真实行号一致），下面是这行的解释。空行不单独列出（它们只负责让代码不挤在一起）。遇到看不懂的代码块，就找它上面的行号回到源文件对照。')
    src_path = os.path.join(ROOT, relpath)
    with open(src_path, encoding='utf-8') as f:
        lines = f.read().splitlines()

    breaks = breaks or {}
    missing = []
    for i, text in enumerate(lines, start=1):
        if i in breaks:
            h2(breaks[i])
        if not text.strip():
            continue
        if i in explains:
            code('第 %d 行 │ %s' % (i, text))
            para(explains[i])
        else:
            missing.append(i)

    if missing:
        print('!! 还缺这些行的解释：%s %s' % (relpath, missing))


def main():
    # 第二~七部分：逐行手册（行号现场从源文件读取）
    line_by_line('src/main.c', MAIN_EXPLAINS,
                 '第二部分 · main.c 逐行手册（全 704 行）', breaks=MAIN_BREAKS)
    line_by_line('tools/make_sample.py', E_SAMPLE,
                 '第三部分 · make_sample.py 逐行手册（全 155 行）')
    line_by_line('Makefile', others.MAKEFILE, '第四部分 · Makefile 逐行手册')
    line_by_line('push.bat', others.PUSHBAT, '第五部分 · push.bat 逐行手册')
    line_by_line('更新文档.bat', others.UPDATEBAT, '第六部分 · 更新文档.bat 逐行手册')
    line_by_line('.gitignore', others.GITIGNORE, '第七部分 · .gitignore 逐行手册')

    # 第八部分：LICENSE 与 README（散文体逐段）
    others.build_license_readme(h1, h2, para, bullet, code, note)

    out = os.path.join(ROOT, 'docs', 'packetlens逐行手册.docx')
    save(out, title='PacketLens 逐行手册', created='2026-10-03 20:33')


if __name__ == '__main__':
    main()
