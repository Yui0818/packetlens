#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_diagrams.py —— 给文档画配图
==================================
用 matplotlib 画出教学示意图，存到 tools/assets/ 下（PNG）。
三份文档（学习笔记/完全教程/逐行手册）会把这些图插进去讲。

运行（Windows 上的 python）：python tools/make_diagrams.py
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.lines import Line2D

# 中文字体（Windows 自带微软雅黑）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 全套配色（和文档的排版一致）
NAVY = '#1B3A5C'
BLUE = '#2A5A84'
LBLUE = '#D6E4F0'
LLBLUE = '#EBF2F9'
GRAY = '#6B6B6B'
LGRAY = '#F4F6F8'
GREEN = '#2E7D5B'
LIME = '#E3F1E8'
AMBER = '#B8860B'
LAMBER = '#FBF3DD'

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets')
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, fc=LBLUE, ec=BLUE, fs=12, tc='#1A1A1A', bold=False):
    """画一个圆角盒子，文字居中。"""
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.06,rounding_size=0.12',
                       fc=fc, ec=ec, lw=1.4)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color=tc,
            fontweight=('bold' if bold else 'normal'))


def arrow(ax, x1, y1, x2, y2, text='', color=BLUE, fs=10.5, ls='-', style='-|>',
          tx=None, ty=None, tc=None):
    """画一根箭头，可带说明文字。"""
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=16,
                        color=color, lw=1.6, linestyle=ls)
    ax.add_patch(a)
    if text:
        ax.text(tx if tx is not None else (x1 + x2) / 2,
                ty if ty is not None else (y1 + y2) / 2 + 0.12,
                text, ha='center', va='bottom', fontsize=fs, color=tc or color)


def new_fig(w, ymin=0, ymax=10):
    """w = 图宽（英寸）。坐标统一用「10 宽 × (ymax-ymin) 高」的方格，
    高度按同一比例自动换算（1 个坐标单位在横竖两个方向一样长）。"""
    h = w * (ymax - ymin) / 10.0
    fig = plt.figure(figsize=(w, h), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(ymin, ymax)
    ax.axis('off')
    return fig, ax


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor='white')
    plt.close(fig)
    print('画出:', name)


# ============================================================
# 图 1：网络分层——套娃式封装
# ============================================================
def d01_encapsulation():
    fig, ax = new_fig(9.6, 0.5, 7.4)
    y = 4.6
    h = 1.5
    box(ax, 0.4, y, 2.2, h, '以太网头\n14 字节', fc=NAVY, ec=NAVY, tc='white')
    box(ax, 2.6, y, 2.4, h, 'IPv4 头\n≥20 字节', fc=BLUE, ec=BLUE, tc='white')
    box(ax, 5.0, y, 2.2, h, 'TCP / UDP / ICMP 头', fc='#5B84A8', ec='#5B84A8', tc='white')
    box(ax, 7.2, y, 2.4, h, '数据\n（负载）', fc=LBLUE, ec=BLUE)
    ax.text(5.0, 6.7, '一个网络包 = 一层套一层', ha='center', fontsize=14,
            color=NAVY, fontweight='bold')
    ax.annotate('链路层', (1.5, 4.5), (1.5, 3.6), ha='center', fontsize=11,
                color=NAVY, arrowprops=dict(arrowstyle='-', color=NAVY))
    ax.annotate('网络层', (3.8, 4.5), (3.8, 3.6), ha='center', fontsize=11,
                color=BLUE, arrowprops=dict(arrowstyle='-', color=BLUE))
    ax.annotate('传输层', (6.1, 4.5), (6.1, 3.6), ha='center', fontsize=11,
                color='#5B84A8', arrowprops=dict(arrowstyle='-', color='#5B84A8'))
    ax.annotate('应用数据', (8.4, 4.5), (8.4, 3.6), ha='center', fontsize=11,
                color=GRAY, arrowprops=dict(arrowstyle='-', color=GRAY))
    ax.text(5.0, 2.9, 'packetlens 的解析顺序就是从最外层往里剥：先看以太网头，再看 IP 头，最后看 TCP/UDP/ICMP。',
            ha='center', fontsize=11, color=GRAY)
    save(fig, 'd01_encapsulation.png')


# ============================================================
# 图 2：解析流程——一层层剥开
# ============================================================
def d02_peeling():
    fig, ax = new_fig(5.6, 0.1, 9.9)
    box(ax, 1.2, 8.4, 7.6, 1.2, '读入一个包的原始字节\n（一串 0 和 1）', fc=LGRAY, ec=GRAY, fs=12)
    arrow(ax, 5.0, 8.4, 5.0, 7.7)
    box(ax, 1.2, 6.5, 7.6, 1.2, '以太网层\ndst MAC(6) + src MAC(6) + 类型(2)', fc=LBLUE, ec=BLUE, fs=11.5)
    arrow(ax, 5.0, 6.5, 5.0, 5.8, text='剥掉 14 字节', fs=10.5)
    box(ax, 1.2, 4.6, 7.6, 1.2, 'IPv4 层\n版本 + TTL + 协议号 + 源/目的 IP', fc=LBLUE, ec=BLUE, fs=11.5)
    ax.text(9.9, 4.05, '读出协议号 →\n决定下一步', fontsize=10, color=AMBER, ha='right', va='top')
    arrow(ax, 5.0, 4.6, 5.0, 3.9, text='剥掉 IP 头（ihl 字节）', fs=10.5)
    box(ax, 1.2, 2.7, 7.6, 1.2, 'TCP / UDP / ICMP 层\n端口、标志、类型…', fc=LBLUE, ec=BLUE, fs=11.5)
    arrow(ax, 5.0, 2.7, 5.0, 2.0)
    box(ax, 1.2, 0.8, 7.6, 1.2, '装进 PacketInfo 档案袋\n→ 打印 / 过滤 / 统计', fc=LIME, ec=GREEN, fs=12)
    ax.text(5.0, 0.28, '每一层先检查「剩下的字节够不够」，不够就优雅退出', ha='center',
            fontsize=10, color=GRAY)
    save(fig, 'd02_peeling.png')


# ============================================================
# 图 3：TCP 三次握手
# ============================================================
def d03_handshake():
    fig, ax = new_fig(7.6, 0.5, 5.3)
    ax.annotate('', (2.0, 1.0), (2.0, 4.2), arrowprops=dict(arrowstyle='-', color=GRAY))
    ax.annotate('', (8.0, 1.0), (8.0, 4.2), arrowprops=dict(arrowstyle='-', color=GRAY))
    box(ax, 0.55, 4.15, 2.9, 0.75, '本机 192.168.1.109', fc=LBLUE, ec=BLUE, fs=11, bold=True)
    box(ax, 6.55, 4.15, 2.9, 0.75, '网站服务器', fc=LBLUE, ec=BLUE, fs=11, bold=True)
    arrow(ax, 2.0, 3.65, 8.0, 3.65, text='① SYN（seq=100）', fs=11, ty=3.72)
    arrow(ax, 8.0, 2.85, 2.0, 2.85, text='② SYN+ACK（seq=1000）', fs=11, ty=2.92)
    arrow(ax, 2.0, 2.05, 8.0, 2.05, text='③ ACK —— 连接建立！', fs=11, ty=2.12, color=GREEN)
    ax.text(5.0, 1.45, '之后开始传数据（PSH+ACK）…… 用完再 FIN 挂断',
            ha='center', fontsize=10.5, color=GRAY)
    ax.text(5.0, 0.75, '示例文件的包 #1、#2 就是前两步', ha='center', fontsize=10, color=AMBER)
    save(fig, 'd03_handshake.png')


# ============================================================
# 图 4：大端 vs 小端
# ============================================================
def d04_endian():
    fig, ax = new_fig(7.8, 0.5, 5.9)
    ax.text(5.0, 5.6, '同一个数字 0x1234，在内存里的两种排法', ha='center',
            fontsize=13.5, color=NAVY, fontweight='bold')
    box(ax, 0.8, 3.4, 1.3, 1.0, '0x12', fc=NAVY, ec=NAVY, tc='white', fs=13)
    box(ax, 2.1, 3.4, 1.3, 1.0, '0x34', fc=NAVY, ec=NAVY, tc='white', fs=13)
    ax.text(3.7, 3.9, '大端（网络字节序）—— 高位在前，网络协议按规定用它', fontsize=11.5,
            color=NAVY, va='center')
    box(ax, 0.8, 1.6, 1.3, 1.0, '0x34', fc=AMBER, ec=AMBER, tc='white', fs=13)
    box(ax, 2.1, 1.6, 1.3, 1.0, '0x12', fc=AMBER, ec=AMBER, tc='white', fs=13)
    ax.text(3.7, 2.1, '小端 —— x86 电脑平时的习惯，低位在前', fontsize=11.5,
            color=AMBER, va='center')
    ax.text(5.0, 0.75, '所以 packetlens 不能直接把字节读成数字，必须用 rd16/rd32 手工按大端拼——这就是那两个小函数的全部意义。',
            ha='center', fontsize=10.5, color=GRAY)
    save(fig, 'd04_endian.png')


# ============================================================
# 图 5：pcap 文件结构
# ============================================================
def d05_pcap():
    fig, ax = new_fig(9.8, 3.1, 7.9)
    box(ax, 0.4, 5.0, 2.6, 2.6, '全局头\n24 字节', fc=NAVY, ec=NAVY, tc='white', fs=13, bold=True)
    ax.text(1.7, 4.55, '魔数 0xA1B2C3D4\n版本 2.4\n时区/精度 0\n最大抓包 65535\n链路类型 1（以太网）',
            ha='center', va='top', fontsize=9.5, color=GRAY)
    for i, (x, tag) in enumerate([(3.3, '#1'), (5.9, '#2')]):
        box(ax, x, 5.9, 1.4, 1.7, '包头\n16B', fc=BLUE, ec=BLUE, tc='white', fs=11)
        box(ax, x + 1.4, 5.9, 1.5, 1.7, '包体\n数据', fc=LBLUE, ec=BLUE, fs=11)
        ax.text(x + 1.45, 5.6, '包 ' + tag, ha='center', fontsize=10, color=GRAY)
    ax.text(8.75, 6.9, '……', ha='center', fontsize=17, color=GRAY)
    ax.text(8.75, 5.75, '直到文件末尾', ha='center', fontsize=10, color=GRAY)
    ax.text(5.0, 4.35, '每个包的 16 字节包头 = 时间戳秒(4) + 微秒(4) + 抓取长度(4) + 原始长度(4)',
            ha='center', fontsize=10.5, color=GRAY)
    ax.text(5.0, 3.35, '一句话：pcap = 一张 24 字节的「封面」+ 一串「16 字节小标签 + 包本体」',
            ha='center', fontsize=11, color=NAVY)
    save(fig, 'd05_pcap.png')


# ============================================================
# 图 6：程序流水线
# ============================================================
def d06_pipeline():
    fig, ax = new_fig(9.8, 0.8, 8.2)
    box(ax, 0.5, 6.6, 2.1, 1.3, '打开输入\n文件 / 网卡', fc=LGRAY, ec=GRAY, fs=12)
    arrow(ax, 2.6, 7.25, 3.3, 7.25, text='每个包', fs=10)
    box(ax, 3.3, 6.6, 2.1, 1.3, 'parse_packet\n解析 → 档案袋', fc=LBLUE, ec=BLUE, fs=11.5)
    arrow(ax, 5.4, 7.25, 6.1, 7.25)
    box(ax, 6.1, 6.6, 1.7, 1.3, 'filter\n过滤', fc=LAMBER, ec=AMBER, fs=11.5)
    arrow(ax, 7.8, 7.25, 8.5, 7.25)
    box(ax, 8.5, 6.6, 1.2, 1.3, '打印', fc=LBLUE, ec=BLUE, fs=11.5)
    arrow(ax, 6.95, 6.6, 6.95, 5.7)
    box(ax, 5.6, 4.4, 2.7, 1.3, 'stats_update\n记账', fc=LBLUE, ec=BLUE, fs=11.5)
    arrow(ax, 6.95, 4.4, 6.95, 3.5)
    box(ax, 4.6, 2.2, 4.7, 1.3, '收尾：emit_stats（屏幕）\n＋ write_report（文件，可选）', fc=LIME, ec=GREEN, fs=11.5)
    ax.text(1.7, 5.6, '这段流水线\nhandle_packet 里\n一字不差地跑', ha='center', fontsize=10.5, color=GRAY)
    ax.annotate('', (3.2, 6.4), (3.2, 4.9), arrowprops=dict(arrowstyle='-', color=GRAY, linestyle='--'))
    ax.text(5.0, 1.1, '离线读文件 和 实时抓网卡 两种模式，共用同一条流水线',
            ha='center', fontsize=11, color=NAVY)
    save(fig, 'd06_pipeline.png')


# ============================================================
# 图 7：Windows 与 WSL 的路径对应
# ============================================================
def d07_wsl_path():
    fig, ax = new_fig(9.6, 3.1, 6.6)
    box(ax, 0.5, 4.0, 4.0, 2.6, '', fc=LGRAY, ec=GRAY)
    ax.text(2.5, 6.15, 'Windows（资源管理器）', ha='center', fontsize=12, color=NAVY, fontweight='bold')
    ax.text(2.5, 5.35, 'D:\\Projects\\packetlens', ha='center', fontsize=12.5, color='#1A1A1A',
            family='monospace')
    ax.text(2.5, 4.55, '（反斜杠 \\ 分层，从盘符开始）', ha='center', fontsize=10, color=GRAY)
    box(ax, 5.5, 4.0, 4.0, 2.6, '', fc='#1E1E1E', ec='#1E1E1E')
    ax.text(7.5, 6.15, 'WSL 终端', ha='center', fontsize=12, color=NAVY, fontweight='bold')
    ax.text(7.5, 5.35, '$ cd /mnt/d/Projects/packetlens', ha='center', fontsize=12,
            color='#7FE08A', family='monospace')
    ax.text(7.5, 4.55, '（正斜杠 / 分层，/mnt/d 就是 D 盘）', ha='center', fontsize=10, color=GRAY)
    arrow(ax, 4.6, 5.3, 5.4, 5.3, text='同一批文件！', fs=11, ty=5.4, color=GREEN, tc=GREEN)
    ax.text(5.0, 3.3, '记住这张图，以后看到 /mnt/d 就知道说的是 D 盘',
            ha='center', fontsize=10.5, color=GRAY)
    save(fig, 'd07_wsl_path.png')


# ============================================================
# 图 8：GitHub 仓库页面示意
# ============================================================
def d08_github():
    fig, ax = new_fig(9.8, 0.2, 9.5)
    box(ax, 0.3, 0.7, 9.4, 8.6, '', fc='white', ec='#C9D3DD', )
    ax.add_patch(Rectangle((0.3, 8.35), 9.4, 0.95, fc='#24292F', ec='none'))
    ax.text(0.7, 8.82, 'github.com', fontsize=11, color='white', va='center')
    ax.text(9.55, 8.82, '搜索…   通知   头像', fontsize=9.5, color='#C9D3DD', va='center', ha='right')
    ax.text(0.75, 7.85, 'Yui0818 / ', fontsize=13, color='#0969DA', va='center')
    ax.text(2.35, 7.85, 'packetlens', fontsize=13, color='#0969DA', va='center', fontweight='bold')
    ax.text(3.65, 7.85, 'Public', fontsize=9, color=GRAY, va='center',
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#C9D3DD'))
    for i, t in enumerate(['Watch', 'Fork', '★ Star']):
        ax.text(7.1 + i * 0.85, 7.85, t, fontsize=9.5, color='#24292F', va='center',
                bbox=dict(boxstyle='round,pad=0.3', fc='#F6F8FA', ec='#C9D3DD'))
    for i, t in enumerate(['Code', 'Issues', 'Pull requests', 'Actions', 'Insights']):
        ax.text(0.75 + i * 1.55, 7.15, t, fontsize=10, color='#24292F', va='center')
    ax.add_patch(Rectangle((0.6, 6.75), 6.3, 0.1, fc='#E8A33D', ec='none'))
    files = [('src/', '能解析协议头了：以太网/IP/TCP/UDP/ICMP', '5 days ago'),
             ('tools/', '加个造测试数据的脚本', '5 days ago'),
             ('samples/', '初始版本：读 pcap 打长度和时间戳', '3 weeks ago'),
             ('docs/', '文档跟上', '3 days ago'),
             ('Makefile', '修个编译警告', '3 weeks ago')]
    for i, (name, msg, when) in enumerate(files):
        y = 6.25 - i * 0.68
        ax.text(0.85, y, name, fontsize=10.5, color='#0969DA', va='center')
        ax.text(2.6, y, msg, fontsize=10, color='#57606A', va='center')
        ax.text(6.7, y, when, fontsize=9.5, color='#57606A', va='center')
    box(ax, 7.3, 2.0, 2.2, 4.5, '', fc='#F6F8FA', ec='#C9D3DD')
    ax.text(7.5, 6.15, 'About', fontsize=10.5, color='#24292F', va='center', fontweight='bold')
    ax.text(7.5, 5.75, '描述、MIT 协议\nStars / 贡献者\n语言构成条\nReleases…', fontsize=9.5,
            color='#57606A', va='top', linespacing=1.6)
    ax.text(0.75, 1.7, 'README 区域：项目说明书\n（一句话定位 + 运行示例 + 功能清单…）', fontsize=10.5,
            color='#24292F', va='top', linespacing=1.6)
    ax.text(5.0, 0.35, '第 7 章会带你逐个区域讲解', ha='center', fontsize=10, color=GRAY)
    save(fig, 'd08_github.png')


# ============================================================
# 图 9：选择排序 4 步演示
# ============================================================
def d09_sort():
    fig, ax = new_fig(9.4, 1.3, 5.5)
    ax.text(5.0, 5.15, '选择排序：每轮从未排序部分挑最大的放到前面（数字 = 出现次数）',
            ha='center', fontsize=12.5, color=NAVY, fontweight='bold')
    steps = [
        ('初始', [('3', 0), ('1', 1), ('3', 2), ('1', 3)]),
        ('第1轮', [('3', 0), ('1', 1), ('3', 2), ('1', 3)]),
        ('第2轮', [('3', 0), ('3', 1), ('1', 2), ('1', 3)]),
        ('完成', [('3', 0), ('3', 1), ('1', 2), ('1', 3)]),
    ]
    for si, (label, cells) in enumerate(steps):
        x0 = 0.62 + si * 2.32
        ax.text(x0 + 0.85, 4.5, label, ha='center', fontsize=10.5, color=GRAY)
        for ci, (num, rank) in enumerate(cells):
            fc = LIME if (si >= 2 and ci < 2) else LBLUE
            ec = GREEN if (si >= 2 and ci < 2) else BLUE
            box(ax, x0 + ci * 0.52, 3.4, 0.48, 0.8, num, fc=fc, ec=ec, fs=12)
        if si < 3:
            arrow(ax, x0 + 2.06, 3.8, x0 + 2.26, 3.8, fs=10)
    ax.text(5.0, 2.35, '绿色 = 已经就位的前两名（Top 榜）；每轮只做「找最大 + 交换」两件事',
            ha='center', fontsize=10.5, color=GRAY)
    ax.text(5.0, 1.5, '数据少的时候这么排最省事；以后数据多了再换快速排序——先跑起来，再优化。',
            ha='center', fontsize=10.5, color=GRAY)
    save(fig, 'd09_sort.png')


# ============================================================
# 图 10：过滤器三道闸门
# ============================================================
def d10_filter():
    fig, ax = new_fig(9.6, 0.6, 5.6)
    box(ax, 0.4, 4.3, 1.9, 1.6, '解析好的\n包（档案袋）', fc=LGRAY, ec=GRAY, fs=11)
    arrow(ax, 2.3, 5.1, 3.0, 5.1)
    gates = [('协议？', 'filter.proto'), ('端口？', 'filter.port'), ('主机？', 'filter.has_host')]
    for i, (t, sub) in enumerate(gates):
        x = 3.0 + i * 2.05
        box(ax, x, 4.35, 1.75, 1.5, t, fc=LAMBER, ec=AMBER, fs=12, bold=True)
        ax.text(x + 0.87, 3.95, sub, ha='center', fontsize=8.5, color=GRAY)
        if i < 2:
            arrow(ax, x + 1.75, 5.1, x + 2.05, 5.1, fs=9)
    arrow(ax, 9.15, 5.1, 9.55, 5.1, text='放行！', fs=10.5, ty=5.2, color=GREEN, tc=GREEN)
    ax.text(5.0, 2.42, '任何一道说「不」：包被跳过（filtered++）', fontsize=10.5, color='#B4544E',
            ha='center', va='top')
    for i in range(3):
        x = 3.85 + i * 2.05
        ax.annotate('', (x, 4.35), (x - 0.35, 2.95), arrowprops=dict(arrowstyle='-|>',
                    color='#B4544E', lw=1.4, linestyle='--'))
    ax.text(1.35, 3.35, '三个条件\n没写 = 不限\n写了必须过', ha='center', fontsize=10,
            color=GRAY, linespacing=1.6)
    ax.text(5.0, 0.9, '例：tcp port 80 —— 闸门 1 只看 TCP，闸门 2 只看沾 80 端口的，闸门 3 不限',
            ha='center', fontsize=10.5, color=NAVY)
    save(fig, 'd10_filter.png')


# ============================================================
# 图 11：版本时间线
# ============================================================
def d11_timeline():
    fig, ax = new_fig(9.8, 1.3, 5.8)
    ax.annotate('', (0.6, 5.0), (9.4, 5.0), arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=2))
    vers = [
        ('v0.1', '读 pcap\n打长度/时间'),
        ('v0.2', '逐层解析\n协议头'),
        ('v0.3', '统计\nTop 排名'),
        ('v0.4', '过滤\n表达式'),
        ('v0.5', '实时抓包\nlive 模式'),
        ('v0.6', '报告导出\n+ 收尾'),
    ]
    for i, (v, t) in enumerate(vers):
        x = 1.05 + i * 1.5
        ax.add_patch(Circle((x, 5.0), 0.09, fc=LBLUE, ec=BLUE, lw=1.6))
        ax.text(x, 5.45, v, ha='center', fontsize=12, color=NAVY, fontweight='bold')
        ax.text(x, 4.6, t, ha='center', va='top', fontsize=9.5, color='#1A1A1A', linespacing=1.5)
    ax.text(5.0, 2.3, '小步慢走：每个版本只加一点点功能，加完就提交、写文档——',
            ha='center', fontsize=11, color=NAVY)
    ax.text(5.0, 1.6, '所以每一行代码你都有机会弄懂，而不是面对一坨写好的工程。',
            ha='center', fontsize=11, color=GRAY)
    save(fig, 'd11_timeline.png')


if __name__ == '__main__':
    d01_encapsulation()
    d02_peeling()
    d03_handshake()
    d04_endian()
    d05_pcap()
    d06_pipeline()
    d07_wsl_path()
    d08_github()
    d09_sort()
    d10_filter()
    d11_timeline()
    print('全部画完，在', OUT)
