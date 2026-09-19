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
    '八、v0.2：解析协议头（以太网 / IPv4 / TCP / UDP / ICMP）逐行讲解',
    '九、下一阶段预告：协议统计、过滤器与实时抓包',
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
code('已经完成：读 pcap 文件、打印基础信息；逐层解析 以太网 / IPv4 / TCP / UDP / ICMP 头（v0.2）\n尚未做：协议统计、过滤器、实时抓包、导出报告')

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
para('查询这个文件的「链路层协议类型」。值为 1 表示以太网（Ethernet）。v0.1 里先把它存着不用；v0.2 起它派上用场——用来提醒「这个文件不是以太网格式的话，解析结果可能不准」。')

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
code('def tcp(payload, sport, dport, seq, flags) / def udp(...) / def icmp(...)')
para('构造 TCP / UDP / ICMP 头。TCP 头通常 20 字节（flags 标志位决定这个包是 SYN、SYN+ACK 还是数据包）；UDP 头 8 字节；ICMP 头 8 字节（type=8 是 ping 请求，type=0 是应答）。')

h2('4.3 生成文件')
code('write_pcap("samples/sample.pcap", packets)')
para('把全局头 + 所有包按字节拼起来写盘。现在的样例一共 6 个包：TCP 握手 2 个 + TCP 数据 1 个 + UDP 1 个 + ICMP ping 请求/应答 2 个，正好覆盖 v0.2 要解析的所有协议。')

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
# 八、v0.2 解析协议头
# ============================================================
h1('八、v0.2：解析协议头（以太网 / IPv4 / TCP / UDP / ICMP）逐行讲解')
para('v0.1 只会数「包多大」；v0.2 开始真正「读懂」包里的内容——像剥洋葱一样，从最外面的以太网头一层层剥进去。')
para('每个包都是按同样的顺序「套娃」的，这也是网络分层最直观的样子：')
code('[以太网头 14 字节][IPv4 头 ≥20 字节][TCP/UDP/ICMP 头][数据]')

h2('8.1 这一步新增了什么')
bullet('以太网头：这个包从哪个网卡来、到哪个网卡去（MAC 地址），上层是什么协议')
bullet('IPv4 头：从哪个 IP 到哪个 IP、上层是 TCP 还是 UDP、还能被转多少跳（TTL）')
bullet('TCP / UDP：从哪个端口到哪个端口；TCP 还带标志位（SYN / ACK / PSH...）')
bullet('ICMP：ping 的请求（type=8）和应答（type=0）')
para('先学会「看懂每个包」，下一阶段（第九章）才能做统计、过滤这些真正有用的功能。')

h2('8.2 大端 / 网络字节序：为什么不能直接读数字')
para('网络协议规定：多字节数字要「高位在前」传（大端 / 网络字节序）。而我们的电脑（x86）平时是「低位在前」（小端）。所以不能直接把一串字节当成数字用，要手工把字节按正确顺序拼起来。')
code('static unsigned int rd16(const unsigned char *p) {\n    return ((unsigned int)p[0] << 8) | p[1];\n}')
para('rd16 = read 2 bytes。p[0] 是第一个字节（在高位），p[1] 是第二个（低位）；「<< 8」就是把一个字节挪到高位去（相当于乘 256），再用「按位或 |」拼起来。')
code('static unsigned int rd32(const unsigned char *p) {\n    return ((unsigned int)p[0] << 24) | ((unsigned int)p[1] << 16) |\n           ((unsigned int)p[2] << 8)  | (unsigned int)p[3];\n}')
para('rd32 同理，一次拼 4 个字节（用在 TCP 序列号这种 4 字节字段上）。')

h2('8.3 把地址打印成人话：MAC 与 IP')
code('static void print_mac(const unsigned char *m) {\n    printf("%02x:%02x:%02x:%02x:%02x:%02x", m[0], m[1], m[2], m[3], m[4], m[5]);\n}')
para('MAC 地址是 6 个字节。%02x 的意思是「用十六进制打印、不足两位补 0」，拼起来就是 aa:bb:cc:dd:ee:ff 这种大家都认识的样子。')
code('static void print_ipv4_addr(const unsigned char *a) {\n    printf("%u.%u.%u.%u", a[0], a[1], a[2], a[3]);\n}')
para('IP 地址就是 4 个字节，每个字节转成十进制、用点隔开——192.168.1.1 在磁盘上其实就是 4 个 0~255 的数字。')

h2('8.4 第一层：以太网头（固定 14 字节）')
code('目的MAC(6)  源MAC(6)  类型(2)')
para('类型字段（ethertype）说明「里面装了什么」：0x0800=IPv4，0x0806=ARP，0x86DD=IPv6。')
code('unsigned int ethertype = rd16(pkt + 12);\nprintf("    以太网  源="); print_mac(pkt + 6);\nprintf("  目的=");      print_mac(pkt);')
para('pkt 是这个包的起点。pkt+6 跳过 6 个字节就是源 MAC 的位置；pkt+12 是类型字段。剥掉这 14 字节，剩下的就是「上层协议的数据」，交给下一步继续剥。')
code('const unsigned char *payload = pkt + 14;   /* 指针加法：跳过 14 个字节 */')

h2('8.5 第二层：IPv4 头（20 字节起步）')
para('IPv4 头比以太网头复杂，但对我们有用的就几个位置：')
code('p+0   版本号(高4位) + 首部长度(低4位)\np+2   总长度(2)\np+6   分片信息(2)\np+8   TTL(1)\np+9   协议号(1)\np+12  源IP(4)\np+16  目的IP(4)')
para('首部长度为什么「单位是 4 字节」？因为它只有 4 个比特（最大 15），15×4=60 字节封顶——这是协议设计时为了省空间想出来的办法。没有选项时首部是 20 字节，有选项时更长，所以要拿 ihl 算出「传输层从哪里开始」。')
code('unsigned int ihl = (p[0] & 0x0F) * 4;\nconst unsigned char *transport = p + ihl;   /* 传输层起点 */')
para('协议号决定下一步解析谁：6=TCP，17=UDP，1=ICMP，程序用 switch 分发。')
note('分片细节：IPv4 允许把大包切成几片传。非第一片里没有传输层头，强行按 TCP 解析会读到垃圾——所以程序检查分片偏移，非 0 就跳过端口解析。')

h2('8.6 第三层：TCP 头的端口与标志位')
code('p+0   源端口(2)\np+2   目的端口(2)\np+4   序列号(4)\np+13  标志位(1)')
para('标志位这 1 个字节的 8 个比特，每位是一个开关：0x02=SYN（我想建连接）、0x10=ACK（我确认收到）、0x08=PSH（请立即交给应用）、0x01=FIN（我想挂断）……')
code('if (f & 0x02) { printf("SYN"); }\nif (f & 0x10) { printf(first ? "ACK" : "+ACK"); }')
para('「&」是按位与：那一位是 1，结果就非 0，说明这个标志开着。程序把开着的标志拼成 SYN / SYN+ACK / PSH+ACK 这种可读形式。')

h2('8.7 第三层：UDP 与 ICMP')
para('UDP 头只有 8 字节：源端口(2) 目的端口(2) 长度(2) 校验和(2)。它比 TCP 简单得多——没有连接、没有重传，发出去就不管了。')
para('ICMP 是网络层的「系统消息」，ping 就是它：type=8 是回显请求，type=0 是回显应答。')
code('ICMP    类型=8（回显请求 / ping）  代码=0')

h2('8.8 边界检查：每层都要先看长度')
para('真实的网络包千奇百怪，还有截断包、畸形包。所以解析每一层之前都要检查「剩下的字节够不够读我要的字段」，不够就打印一行提示、直接返回——绝不能让程序读到缓冲区外面去（那会崩溃，甚至出安全漏洞）。')
code('if (len < 20) {\n    printf("    IPv4    头部不完整（只有 %u 字节）\\n", len);\n    return;\n}')
para('这就是为什么每个解析函数都带着 len 参数：不是不信任数据，而是「凡是外部输入，一律先验后用」。')

h2('8.9 跑一遍看看')
code('#1  时间=1700000000.000100  长度=54\n    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)\n    IPv4    源=192.168.1.109  目的=93.184.216.34  协议=TCP(6)  TTL=64\n    TCP     源端口=54321  目的端口=80  序列号=100  标志=SYN\n#2  时间=1700000000.000200  长度=54\n    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)\n    IPv4    源=93.184.216.34  目的=192.168.1.109  协议=TCP(6)  TTL=64\n    TCP     源端口=80  目的端口=54321  序列号=1000  标志=SYN+ACK\n#3  时间=1700000000.000300  长度=79\n    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)\n    IPv4    源=93.184.216.34  目的=192.168.1.109  协议=UDP(17)  TTL=64\n    UDP     源端口=53  目的端口=50000  长度=45\n#4  时间=1700000000.000400  长度=101\n    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)\n    IPv4    源=192.168.1.109  目的=93.184.216.34  协议=TCP(6)  TTL=64\n    TCP     源端口=54321  目的端口=80  序列号=200  标志=PSH+ACK\n#5  时间=1700000000.000500  长度=74\n    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)\n    IPv4    源=192.168.1.109  目的=192.168.1.1  协议=ICMP(1)  TTL=64\n    ICMP    类型=8（回显请求 / ping）  代码=0\n#6  时间=1700000000.000600  长度=74\n    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)\n    IPv4    源=192.168.1.1  目的=192.168.1.109  协议=ICMP(1)  TTL=64\n    ICMP    类型=0（回显应答 / ping 回复）  代码=0\n--- 文件读取完毕 ---\n共 6 个包，总流量 436 字节')
para('对照着看：包 1、2 是 TCP 三次握手的前两步（SYN → SYN+ACK），包 3 是 UDP（来自 DNS 端口 53），包 4 是带数据的 TCP 包（PSH+ACK），包 5、6 是 ping 的请求和应答——和 make_sample.py 里构造的 6 个包一一对应。')

# ============================================================
# 九、下一阶段预告
# ============================================================
h1('九、下一阶段预告：协议统计、过滤器与实时抓包')
para('会把包「读懂」之后，下一步就是让这些信息真正有用起来：')
bullet('按协议统计流量占比（TCP / UDP / ICMP 各占多少包、多少字节）')
bullet('Top IP / Top 端口排名（谁在跟谁说话、哪个服务通信最多）')
bullet('过滤表达式（比如只看 tcp port 80，其他包直接无视）')
bullet('直接抓实时网卡流量（不再只读离线文件）')
note('每完成一个阶段，就跑一次 python3 tools/make_doc.py 刷新本文档；后面的每一步都会继续往这里追加章节。')

# ============================================================
# 保存
# ============================================================
import os
os.makedirs('docs', exist_ok=True)
doc.save('docs/pcaptool学习笔记.docx')
print('已生成 docs/pcaptool学习笔记.docx')
