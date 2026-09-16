#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《pcaptool 学习笔记》Word 文档
====================================
这是一个持续更新的学习笔记，把你从零开始学网络、写着这个 C 项目
的所有步骤、每行代码含义都整理成 Word。

每次项目有新的进展（比如解析到了 TCP 头部），就按同样的格式往下追加
章节，然后重新运行本脚本，就会生成最新的完整文档。

运行：python3 tools/make_doc.py
输出：docs/pcaptool学习笔记.docx
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# 创建一个空白文档
doc = Document()

# 设置一个好看的中文字体（正文微软雅黑）
normal = doc.styles['Normal']
normal.font.name = 'Microsoft YaHei'
normal.font.size = Pt(11)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')


# ---------- 工具函数 ----------
def h1(text):
    doc.add_heading(text, level=1)


def h2(text):
    doc.add_heading(text, level=2)


def h3(text):
    doc.add_heading(text, level=3)


def para(text, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    return p


def code(text):
    """代码块：用等宽字体"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = 'Consolas'
    r.font.size = Pt(10)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    return p


def bullet(text):
    doc.add_paragraph(text, style='List Bullet')


def note(text):
    """提示框：灰色斜体"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = True
    r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
    return p


# ============================================================
# 封面
# ============================================================
title = doc.add_heading('pcaptool 项目学习笔记', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.add_run('一个用 C 语言从零实现的网络抓包/分析工具\n作者：刘梓涵（Yui0818）· 南大电院 2025 级').font.size = Pt(12)

para('')
note('本笔记随项目持续更新。每完成一个阶段，都会新增对应章节，由浅入深讲解网络协议。')
doc.add_page_break()

# ============================================================
# 目录
# ============================================================
h1('目录')
for i, t in enumerate([
    '一、项目是什么',
    '二、开发环境与工具',
    '三、v0.1 最小 demo（读 pcap 文件）逐行讲解',
    '四、改造脚本：make_sample.py 逐行讲解',
    '五、构建与运行（Makefile 逐行讲解）',
    '六、项目结构总览',
    '七、Git 与 GitHub 完整流程（含推送、署名）',
    '八、下一阶段预告：解析网络协议头',
]):
    para(f'{i+1}. {t}')
doc.add_page_break()

# ============================================================
# 一、项目是什么
# ============================================================
h1('一、项目是什么')
para('pcaptool 是一个用 C 语言写成的命令行网络抓包 / 分析工具，功能类似于内置版 tcpdump 和 Wireshark。')
para('它做的事情是：')
bullet('读取网络抓包文件（.pcap 格式）')
bullet('逐个解析其中的数据包')
bullet('分析协议类型、端口、地址，做统计')
bullet('最终能实时抓网卡流量、按条件过滤、输出报告')

h2('为什么值得做')
bullet('契合电子信息专业：网络是核心方向')
bullet('C 语言的最佳实战：位操作、内存、字节序、数据结构')
bullet('解决真实问题：网络工程师 / 开发者排查网络问题的刚需')
bullet('基于 libpcap（Wireshark / tcpdump 底层同款），有伟大开源可学')

h2('目前进度')
code('已经完成：读 pcap 文件，打印每个包的长度和时间戳、统计总数\n尚未做：解析 IP/TCP/UDP 头、过滤、统计、实时抓包')

# ============================================================
# 二、开发环境
# ============================================================
h1('二、开发环境与工具')
bullet('操作系统：Windows 11（宿主机）')
bullet('开发：WSL2 里的 Ubuntu 24.04，用 gcc 13.3 编译')
bullet('抓包库：libpcap（Ubuntu 下用 apt 安装，命令：sudo apt install libpcap-dev）')
bullet('测试数据：用 Python 脚本自己生成的 .pcap 文件')
bullet('版本控制：git + GitHub（账号 Yui0818）')

# ============================================================
# 三、main.c 逐行讲解
# ============================================================
h1('三、v0.1 最小 demo（读 pcap 文件）逐行讲解')

h2('3.1 核心思想')
para('这个程序只做一件事：打开一个 pcap 文件，读到里面每一个网络包，报出它的长度和接收时间。')

h2('3.2 include（引入头文件）')
code('#include <stdio.h>')
para('把「标准输入输出」头文件引进来。printf / fprintf 这些往屏幕上打字的功能都靠它。')
code('#include <pcap/pcap.h>')
para('把「libpcap 抓包库」的头引进来。里面声明了读 pcap 文件、抓网卡要用到的所有函数。')

h2('3.3 main 入口与参数')
code('int main(int argc, char *argv[])')
para('程序的入口。argc 是「命令行参数个数」，argv 是「这些参数的内容」。')
code('比如运行  ./pcaptool xxx.pcap\n则  argc=2\n    argv[0]="./pcaptool"   （程序自己）\n    argv[1]="xxx.pcap"     （第一个参数，文件路径）')

h2('3.4 检查参数')
code('if (argc < 2) {')
para('如果用户连文件名都没给（参数太少），就打印用法并退出。')
code('fprintf(stderr, "用法: %s <pcap文件>\\n", argv[0]);\nreturn 1;')
para('stderr 是「错误输出流」，用于报错。return 1 表示程序用「失败」状态退出（非 0 即失败）。')

h2('3.5 打开 pcap 文件')
code('char errbuf[PCAP_ERRBUF_SIZE];')
para('PCAP_ERRBUF_SIZE 是 libpcap 定义的定长缓冲区大小（128）。errbuf 用来放「万一出错，错误原因是什么」。')
code('pcap_t *handle = pcap_open_offline(argv[1], errbuf);')
para('pcap_open_offline 打开一个「离线 pcap 文件」（不是抓活动网卡）。返回句柄 handle（指向该文件的指针）。打不开就返回 NULL，并把原因写到 errbuf。')
code('if (handle == NULL) { ... return 1; }')
para('检查句柄：如果打不开，报错退出。')

h2('3.6 得到链路层类型')
code('int linktype = pcap_datalink(handle);')
para('查询这个文件的「链路层协议类型」。值为 1 表示以太网（Ethernet）。本阶段还没用到，后面解析时用。')

h2('3.7 主循环：读每个包')
code('struct pcap_pkthdr *header;\nconst u_char *packet;')
para('header 会指向「这个包的信息」（长度、时间），packet 会指向「包的原始字节数据」。')
code('while (1) {\n    int ret = pcap_next_ex(handle, &header, &packet);')
para('pcap_next_ex 读「下一个」包，返回值三种：')
bullet('1 = 成功读到一个包')
bullet('-1 = 出错')
bullet('-2 = 文件读完')
code('if (ret == 1) {\n    total++;\n    bytes += header->len;\n    printf("%lld\\t%lu.%06lu\\t%u\\n", total, ts.tv_sec, ts.tv_usec, header->len);\n}')
para('成功读到包时：总数+1，累加字节；header->len 是包长度；ts.tv_sec 是秒、ts.tv_usec 是微秒。')

h2('3.8 汇总与收尾')
code('printf("共 %lld 个包，总流量 %llu 字节\\n", total, bytes);\npcap_close(handle);\nreturn 0;')
para('打印统计，关闭文件释放资源，成功返回 0（0 表示成功）。')

# ============================================================
# 四、make_sample.py 讲解
# ============================================================
h1('四、改造脚本：make_sample.py 逐行讲解')
para('因为我们不想依赖外网下载示例文件，就用 Python 自己生成一个「格式合法」的 pcap 文件。')

h2('4.1 pcap 文件格式')
para('pcap 文件有两层结构：')
bullet('全局头（24 字节）：说明这是 pcap、版本、时间精度、链路层类型')
bullet('若干数据包：每个 = 16 字节包头（时间戳秒/微秒/长度）+ 原始字节数据')
code('全局头：a1 b2 c3 d4  02 00  04 00  00 00 00 00  00 00 00 00  ff ff 00 00  01 00 00 00\n魔数     maj  min        时区(0)  时间精度(0)  最大抓包长度  链路类型')

h2('4.2 核心函数')
code('struct.pack("<IHHiIII", MAGIC, ...)')
para('struct.pack 把 Python 数字「打包」成指定字节序列（写到磁盘的二进制）。< 表示小端字节序（网络包默认小端）。')
code('def eth_frame(payload, src_mac, dst_mac, ethertype):')
para('给一段数据套上「以太网帧头」（14 字节：目标 MAC 6 + 源 MAC 6 + 类型 2）。type=0x0800 是 IPv4，0x0806 是 ARP。')
code('def ipv4(payload, src, dst, proto, ident):')
para('构造 IPv4 头（20 字节）+ 负载。proto：6=TCP，17=UDP，1=ICMP。')
code('def tcp(payload, sport, dport, seq) / def udp(...):')
para('构造 TCP / UDP 头。TCP 头通常 20 字节，UDP 头 8 字节。')

h2('4.3 生成文件')
code('write_pcap("samples/sample.pcap", packets)')
para('把全局头 + 所有包按字节拼起来写盘。')

# ============================================================
# 五、Makefile 讲解
# ============================================================
h1('五、构建与运行（Makefile 逐行讲解）')
para('Makefile 用来告诉编译器「怎么把我的代码变成可执行程序」。')
code('CC = gcc              # 用哪个编译器\nCFLAGS = -Wall -Wextra -O2   # 编译选项（打开警告、二级优化）\nLIBS = -lpcap          # 链接 libpcap 库\n\nall: pcaptool\npcaptool: src/main.c\n\t$(CC) $(CFLAGS) -o pcaptool src/main.c $(LIBS)\n\nclean:\n\trm -f pcaptool')
para('执行 make：编译生成 pcaptool。执行 make clean：删掉编译产物。')

# ============================================================
# 六、项目结构
# ============================================================
h1('六、项目结构总览')
code('pcaptool/\n├── src/main.c            # 主程序（C）\n├── tools/make_sample.py  # 生成测试 pcap\n├── tools/make_doc.py     # 生成学习文档\n├── samples/sample.pcap   # 示例数据\n├── Makefile              # 编译脚本\n├── push.bat              # 一键提交+推送备份脚本\n├── .gitignore            # git 忽略哪些文件\n└── README.md             # 项目说明')

# ============================================================
# 七、Git 与 GitHub
# ============================================================
h1('七、Git 与 GitHub 完整流程（含推送、署名）')
para('下面是你已经走过的完整流程，以后改代码就照这个来。')

h2('7.1 本地提交')
code('git init                 # 初始化仓库\ngit add -A              # 把改动加进暂存区\ngit commit -m "说明"    # 正式打一个提交')

h2('7.2 推到 GitHub')
code('gh repo create pcaptool --public --source=. \n    --push --description "..."')
para('在 GitHub 账号下建公开仓库并推送。')

h2('7.3 署名要点（让你的贡献者只有你自己）')
para('GitHub 是根据提交的 email 来判断「这个提交属于哪个账号」的。要让仓库只认你，必须用你账号的 noreply 邮箱。')
code('git config user.name "Yui0818"\ngit config user.email "324952380+Yui0818@users.noreply.github.com"')
para('这样提交才会挂到你的账号、显示你的头像，contributors 列表才会只有你一个。')

h2('7.4 一键备份脚本（push.bat）')
para('以后改完代码，双击项目目录里的 push.bat，它就会自动：')
bullet('git add 所有改动')
bullet('以 Yui0818 身份提交（不含 AI 署名）')
bullet('通过本机代理推送到 GitHub')
note('GitHub 本身就是最可靠的云端备份。改完代码推上去，就是完成了备份。')

# ============================================================
# 八、下一阶段预告
# ============================================================
h1('八、下一阶段预告：解析网络协议头')
para('v0.1 只是把「每个包的长度」读出来了。下一阶段（阶段 2）要真正「读懂」包的内容：')
bullet('解析以太网头：源 MAC、目标 MAC、协议类型')
bullet('解析 IP 头：源 IP、目标 IP、协议号、TTL')
bullet('解析 TCP 头：源端口、目的端口、序列号、标志位')
bullet('解析 UDP 头：源端口、目的端口、长度')
bullet('识别 ARP / ICMP 等更多协议')
para('这是整个项目最核心、技术上最值钱的部分，也是简历上真正能写「用 C 实现协议解析」的地方。')
note('写到这里，后面的每一步都会继续往本文档追加章节。')

# ============================================================
# 保存
# ============================================================
import os
os.makedirs('docs', exist_ok=True)
doc.save('docs/pcaptool学习笔记.docx')
print('已生成 docs/pcaptool学习笔记.docx')
