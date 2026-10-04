# -*- coding: utf-8 -*-
"""第 4 章（上）：main.c 逐行详解——文件头、工具函数、PacketInfo。"""

from docbuild import *

h1('第 4 章  main.c 逐行详解（上）')

para('这是全书最长、也最重要的部分。main.c 一共 700 多行，我们会一节一节地过，每一行都讲清楚「它在干嘛、为什么这么写」。不用背——写代码从来不是靠背的；看懂思路，需要时回来查。')

para('阅读姿势建议：把代码在屏幕上打开（VS Code 或 GitHub 在线都行），左边代码、右边本文档，一段段对照着看。代码分段和文档小节一一对应，找起来很快。')

h2('4.0 先说明两件小事')
bullet('代码里的「行号」在文档里只是大致参考。以后你再改代码，行号会变，但每段代码的样子不会变——按代码内容找，不按行号找。')
bullet('C 语言是「从上往下」读的：变量、函数都讲究「先定义后使用」。所以文件的结构是：先放工具函数，再放解析函数，最后才是 main（主函数）。')

h2('4.1 文件开头的注释块：给未来的自己留张便条')

para('文件第 1 行到第 21 行是一整块注释（/* 和 */ 夹起来的内容，C 语言会完全无视它们，纯给人看的）。它的内容分两部分。')

para('第一部分是「版本史记」——记录这个项目走到哪一步了：')
code('/*\n'
     ' * packetlens —— 命令行网络抓包分析工具\n'
     ' * 第一阶段（v0.1）：读取一个 pcap 文件，打印每个包的长度和时间戳。\n'
     ' * 第二阶段（v0.2）：把每个包逐层"拆开"解析——以太网 → IPv4 → TCP/UDP/ICMP，\n'
     ' *                  打印源/目的地址、协议、端口、TCP 标志位等信息。\n'
     ' * ...（后续每个版本一行，一直到 v0.6）\n'
     ' */')
para('逐句读：第一行给程序起名（packetlens）和定位（命令行网络抓包分析工具）；后面每行记一个版本的新增能力。为什么值得写？因为三个月后你自己都会忘记「当时为什么这么改」——注释就是留给未来自己的便条。')

para('第二部分是「这个程序干什么」的四句话清单：')
code(' * 这个程序是我们整个项目的起点，它做的事情：\n'
     ' *   1. 打开一个 pcap 文件（pcap 是网络抓包的标准文件格式）\n'
     ' *   2. 一个一个地读出里面的网络包\n'
     ' *   3. 把每个包的长度、接收时间打印出来，并逐层解析协议头（v0.2）\n'
     ' *   4. 统计协议流量占比和 Top IP / 端口（v0.3）')
para('这四句话就是整个程序的地图。看代码迷路时，回到开头看这四句，就想起「哦，整体是在干这四件事」。')

para('最后一句是写给你的话：')
code(' * 看不懂没关系，我会在下方每一行都给注释。先把它跑起来，感受一下。')
para('这句话现在兑现了——你正在读的就是「每一行的注释」的加长版。')

h2('4.2 include：程序的「外援名单」')

para('接下来四行 include：')
code('#include <stdio.h>       /* printf / fprintf：向屏幕打印文字 */\n'
     '#include <stdlib.h>      /* atoi：把命令行里的文字数字转成整数 */\n'
     '#include <string.h>      /* strcmp：比较两个字符串是不是一样 */\n'
     '#include <pcap/pcap.h>   /* libpcap：全世界通用的抓包库 */')
para('include 的意思是「把某个工具箱的说明书复印进来」。C 语言本身只会算数、判断、循环这些基本功——想「打印文字」「比较字符串」「读 pcap 文件」，都要借用别人写好的工具，而工具的名字和用法写在「头文件」里。')

para('逐行解释：')
bullet('stdio.h（standard input/output）= 标准输入输出工具箱。printf（打印文字到屏幕）、fprintf（打印到文件或错误流）都来自它。')
bullet('stdlib.h（standard library）= 通用工具箱。本程序借用了 atoi——把「80」这种文字形式的数字转成真正的整数 80。')
bullet('string.h = 处理文字的工具箱。本程序借用了 strcmp——比较两段文字是不是完全相同（后面解析命令行的「tcp」「port」等关键词时要用）。')
bullet('pcap/pcap.h = 抓包库 libpcap 的说明书。读 pcap 文件、开网卡抓包的函数全在里面。')

note('一个小知识：include 只是「声明外援」，函数真正搬进来是在编译的最后一步「链接」——所以编译命令的结尾有 -lpcap，就是告诉链接器「把 libpcap 接上」。')

h2('4.3 rd16 / rd32：手工拼字节的两个小函数')

para('这是第一个「自己写的工具」，专门解决第 2.9 节讲的「大端小端」问题。完整代码：')
code('static unsigned int rd16(const unsigned char *p) {\n'
     '    return ((unsigned int)p[0] << 8) | p[1];\n'
     '}\n'
     '\n'
     'static unsigned int rd32(const unsigned char *p) {\n'
     '    return ((unsigned int)p[0] << 24) | ((unsigned int)p[1] << 16) |\n'
     '           ((unsigned int)p[2] << 8)  | (unsigned int)p[3];\n'
     '}')

para('先逐词解释函数签名这一行（以 rd16 为例）：')
bullet('static：表示「这个函数只在本文件里用」，外面看不见。以后代码拆成多文件时，static 能防止名字撞车。先记住它是个「内部限定词」即可。')
bullet('unsigned int：函数返回值的类型——一个非负整数（0 到 42 亿）。rd16 拼出来的数字就是这种。')
bullet('rd16：函数名，读作 read 16，意思是「读 2 个字节拼成 1 个 16 位的数」。16 位 = 2 字节。')
bullet('(const unsigned char *p)：参数。p 是一个指针——「指向内存某处的箭头」。它的类型是 unsigned char（每个字节 0~255，代表原始字节最合适）。const 表示只读：这个函数承诺不改动别人给我的数据。')

para('再看函数体里那一行（全文的精华）：')
code('return ((unsigned int)p[0] << 8) | p[1];')
bullet('p[0]：指针 `p` 指向的第一个字节（下标从 0 数起，这是 C 语言传统）。比如网络里收到 0x12 0x34 两个字节，p[0] 是 0x12。')
bullet('<< 8：左移 8 位，等价于「乘以 256」。作用是把第一个字节挪到「高位」去——因为网络是大端，第一个字节代表高位。')
bullet('(unsigned int)：把结果明确成「无符号整数」再移位，避免小数字类型搬家时出意外（一个让你少踩坑的保险）。')
bullet('| p[1]：按位或。把第二个字节（低位）拼上来。拼好之后 0x12 和 0x34 就合成了数字 0x1234。')
para('所以 rd16 做的就是这个翻译：磁盘上的 [12][34] → 它心中的「一千二百三十四（十六进制）」。')

para('rd32 是同一个思路，一次拼 4 个字节：')
bullet('p[0] 左移 24 位（最高位）、p[1] 左移 16 位、p[2] 左移 8 位、p[3] 原地不动（最低位）')
bullet('四段用 | 拼在一起，得到一个 32 位（4 字节）的数。TCP 的序列号、IP 地址都会用到它')
note('为什么 Python 里不用这么麻烦？因为 Python 替你把字节序的事包办了。C 语言「什么都自己来」，所以看得见底层——这正是我们说 C 是「硬核训练场」的原因。')

h2('4.4 地址的四个翻译官')

para('网络包里的地址是「一坨字节」，人类习惯的是点分十进制（IP）和冒号十六进制（MAC）。下面四个函数负责在两者之间来回翻译。')

h3('print_mac：把 6 个字节打印成 aa:bb:cc:dd:ee:ff')
code('static void print_mac(const unsigned char *m) {\n'
     '    printf("%02x:%02x:%02x:%02x:%02x:%02x", m[0], m[1], m[2], m[3], m[4], m[5]);\n'
     '}')
bullet('static void：没有返回值的函数（void = 空）。它的工作是「打印」，打印完就完事，不用返回东西。')
bullet('printf 的第一段是「格式模板」，%02x 出现六次，每个吃掉后面的一个参数：% 表示「这里要填个值」，02 表示「至少两位、不足补 0」，x 表示「十六进制小写」。')
bullet('m[0] 到 m[5] 就是那 6 个字节。连起来就成了 00:11:22:33:44:55 这种大家认识的样子。')

h3('print_ipv4_addr：4 个字节 → 192.168.1.1')
code('static void print_ipv4_addr(const unsigned char *a) {\n'
     '    printf("%u.%u.%u.%u", a[0], a[1], a[2], a[3]);\n'
     '}')
bullet('%u 表示「填一个无符号十进制整数」。四个字节各印一段，中间用点连起来。')
bullet('在磁盘上 IP 就是 4 个 0~255 的数：192、168、1、1。这个函数只是把「电脑的存法」翻译成「人类的读法」。')

h3('ip_to_key 与 print_ip_from_key：给 IP 编「档案号」')
code('static unsigned int ip_to_key(const unsigned char *a) {\n'
     '    return ((unsigned int)a[0] << 24) | ((unsigned int)a[1] << 16) |\n'
     '           ((unsigned int)a[2] << 8)  | a[3];\n'
     '}')
para('ip_to_key 把 4 个字节拼成一个数字——和 rd32 是一模一样的拼法！为什么又写一个？因为「名字表达了用途」：统计功能需要给每个 IP 发一个「档案号」（key），好放进一张「每个 IP 出现过几次」的表里。用它拼出来的数字当档案号，比直接拿 4 个字节到处传方便。')
code('static void print_ip_from_key(FILE *out, unsigned int key) {\n'
     '    fprintf(out, "%u.%u.%u.%u",\n'
     '            (key >> 24) & 0xFF, (key >> 16) & 0xFF, (key >> 8) & 0xFF, key & 0xFF);\n'
     '}')
para('print_ip_from_key 是反方向：把档案号还原成 IP 打印。重点看「取一段」的手法：')
bullet('key >> 24：把数字整体右移 24 位，原来的「最高位那一段」就挪到了最低位')
bullet('& 0xFF：和 11111111 做按位与，只保留最低 8 位，其余全清零——也就是「只取这一段字节」')
bullet('四段依次取出来打印，中间加点。')
para('另外注意这个函数比别的打印函数多了一个参数 FILE *out——这是 v0.6 的改进：打印目的地可以从「屏幕」换成「文件」，让同一份统计既能打屏又能写报告。第 4 章后面讲到 emit_stats 时还会遇到它。')

h2('4.5 起名字的三个翻译官')

h3('proto_name 和 ethertype_name：数字 → 名字')
code('static const char *proto_name(unsigned int proto) {\n'
     '    switch (proto) {\n'
     '        case 6:  return "TCP";\n'
     '        case 17: return "UDP";\n'
     '        case 1:  return "ICMP";\n'
     '        default: return "其它";\n'
     '    }\n'
     '}')
bullet('返回类型 const char *：注意，这次返回的不是数字，而是「一段文字」（C 里的文字是字符数组，char * 指向它）。const 表示这段文字只读。')
bullet('switch…case：多分支判断——proto 等于 6 就返回 "TCP"，等于 17 就返回 "UDP"……一个数字进来，一个名字出去。')
bullet('default：所有 case 都没中的兜底，返回「其它」。永远给 switch 留个兜底是好习惯。')
para('ethertype_name 结构完全相同，只是翻译的是「以太网类型字段」：0x0800 → IPv4、0x0806 → ARP、0x86DD → IPv6。')

h3('print_tcp_flags：一个字节拆成八个人的开关')
code('static void print_tcp_flags(unsigned char f) {\n'
     '    int first = 1;   /* 控制 "+" 加号：第一个标志前面不加 */\n'
     '    if (f & 0x02) { printf("SYN"); first = 0; }\n'
     '    if (f & 0x01) { printf(first ? "FIN" : "+FIN"); first = 0; }\n'
     '    if (f & 0x04) { printf(first ? "RST" : "+RST"); first = 0; }\n'
     '    if (f & 0x08) { printf(first ? "PSH" : "+PSH"); first = 0; }\n'
     '    if (f & 0x10) { printf(first ? "ACK" : "+ACK"); first = 0; }\n'
     '    if (f & 0x20) { printf(first ? "URG" : "+URG"); first = 0; }\n'
     '    if (first)    { printf("（无）"); }\n'
     '}')
para('这是第 2.6 节讲过的东西在代码里的样子：TCP 标志位是一个字节的 8 个开关。怎么判断某个开关开没开？用「按位与」：')
bullet('f & 0x02：0x02 的二进制是 00000010，只有第 2 位是 1。和 f 做按位与，结果非 0 就说明「f 的这一位也是 1」，也就是 SYN 开关开着。')
bullet('first 变量：控制加号。第一个打印出来的标志前面不加 +，后面的都加——所以两个标志会显示成 SYN+ACK 而不是 +SYN+ACK。')
bullet('first ? "FIN" : "+FIN"：三元表达式，读作「first 为真就选前者，否则选后者」，是 if…else 的简写。')
bullet('最后一行：如果一个标志都没开，打印「（无）」，免得输出空荡荡让人困惑。')
note('顺序有讲究：判断的顺序是 SYN → FIN → RST → PSH → ACK → URG，这是业界习惯的书写顺序，所以 SYN+ACK 会按这个规则显示成 SYN+ACK、PSH+ACK——和你用 tcpdump 看到的一致。')

h2('4.6 PacketInfo：一个包的「档案袋」')

para('接下来是全项目最重要的一个结构体（struct）。先看 v0.3 为什么需要它，再看它的每个字段。')

para('v0.2 的时候，解析代码是「边解析边打印」——解析到哪层就打印哪层。但 v0.3 的统计功能也需要这些解析结果，总不能把包再解析一遍吧？于是进行了重构：解析的结果先全部装进一个「档案袋」，谁需要谁来读。这个档案袋就是 PacketInfo：')
code('typedef struct {\n'
     '    /* 以太网层 */\n'
     '    unsigned char mac_src[6];\n'
     '    unsigned char mac_dst[6];\n'
     '    unsigned int  ethertype;\n'
     '\n'
     '    /* IPv4 层 */\n'
     '    int           has_ipv4;\n'
     '    unsigned char ip_src[4];\n'
     '    unsigned char ip_dst[4];\n'
     '    unsigned int  proto;\n'
     '    unsigned int  ttl;\n'
     '\n'
     '    /* 传输层 */\n'
     '    int           has_ports;\n'
     '    unsigned int  sport, dport;\n'
     '    unsigned int  udp_len;\n'
     '    unsigned int  tcp_seq;\n'
     '    unsigned int  tcp_flags;\n'
     '    unsigned int  icmp_type, icmp_code;\n'
     '\n'
     '    /* 给打印用的一句话备注 */\n'
     '    const char   *note;\n'
     '} PacketInfo;')

para('typedef struct 的语法拆解：')
bullet('struct = 「把几个变量捆成一捆」的定义（结构体）。')
bullet('typedef = 「给这个捆起个类型名」，起名叫 PacketInfo。以后写 PacketInfo info; 就等于声明了一个这种捆的变量。')
bullet('大括号里每行是一个「字段」：先写类型，再写字段名，分号结尾。')

para('逐组看字段是怎么对应网络层次的：')
bullet('mac_src[6] / mac_dst[6]：源/目的 MAC 地址，各 6 个字节的数组')
bullet('ethertype：以太网类型字段（0x0800 表示里面是 IPv4）')
bullet('has_ipv4：一个「开关」，1 = 成功解析出了 IPv4 头。为什么需要开关？因为有的包可能不是 IPv4（比如 ARP），或者包被截断了——那时后面的 ip_src 等字段就是没有意义的。这种「开关 + 数据」的写法在解析类代码里非常常见')
bullet('ip_src[4] / ip_dst[4]：源/目的 IP，各 4 个字节')
bullet('proto：协议号（6/17/1），ttl：生存时间')
bullet('has_ports：又一个开关，1 = 解析出了端口（只有 TCP/UDP 才有端口）')
bullet('sport / dport：源/目的端口；udp_len：UDP 头里的长度字段；tcp_seq：TCP 序列号；tcp_flags：TCP 标志位')
bullet('icmp_type / icmp_code：ICMP 的类型和代码（ping 请求是 8，应答是 0）')
bullet('note：一个「小备注」字符串指针（没备注时是 NULL，表示空）。有些包存在异常情况（比如「头部不完整」），解析函数把原因写在这里，打印函数照着念')

para('注意字段名后缀的规律：src = source（来源）、dst = destination（目的）。以后在别的代码里看到 src/dst，都是这个意思。')

para('本章（上篇）到此结束。下一节开始啃最核心的 parse_packet 函数——那才是真正「拆包」手艺的所在。')
