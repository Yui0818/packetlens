# -*- coding: utf-8 -*-
"""第 4 章（中）：main.c 逐行详解——parse_packet 拆包核心。"""

from docbuild import *

h1('第 4 章  main.c 逐行详解（中）')

h2('4.7 parse_packet（一）：函数签名与「先清零」')

para('parse_packet 是整个项目的心脏：把一包原始字节「拆」成 PacketInfo 档案袋。它约 90 行，我们分五段讲。第一段是签名和初始化：')

code('static int parse_packet(const unsigned char *pkt, unsigned int len, PacketInfo *info) {\n'
     '    info->has_ipv4 = 0;\n'
     '    info->has_ports = 0;\n'
     '    info->note = NULL;')

para('逐项解释：')
bullet('static int：这个函数返回一个整数，用来表示「解析成功还是失败」（1 = 成功、0 = 失败）。')
bullet('const unsigned char *pkt：指向这个包的原始字节（只读，解析不能改数据）。')
bullet('unsigned int len：这个包有多少字节。为什么要单独传长度？因为 C 里的指针只记「从哪开始」，不记「有多长」——长度必须自己传进来。')
bullet('PacketInfo *info：指向调用者的档案袋。「填档案」是原地修改，所以传指针（传地址），而不是把整个档案袋复制一份。')
bullet('接下来的三行是「先清零」：has_ipv4、has_ports 置为 0，note 置为 NULL（空）。为什么？因为档案袋在内存里可能残留上次的旧数据，先统一写成「什么都没有」，后面解析到什么再填什么。这是一种防御性习惯，能避免「读到垃圾值」的玄学 bug。')

h2('4.8 parse_packet（二）：搬运以太网头')

code('    if (len < 14) {\n'
     '        return 0;\n'
     '    }\n'
     '    int i;\n'
     '    for (i = 0; i < 6; i++) {\n'
     '        info->mac_dst[i] = pkt[i];\n'
     '        info->mac_src[i] = pkt[i + 6];\n'
     '    }\n'
     '    info->ethertype = rd16(pkt + 12);')

bullet('if (len < 14) return 0;：第一个「边界检查」。以太网头固定 14 字节，如果一个包连 14 字节都不到，根本没法解析——直接报告失败（返回 0）。宁可失败，绝不越界读内存。')
bullet('int i; 然后 for (i = 0; i < 6; i++)：一个数到 6 的小循环。')
bullet('info->mac_dst[i] = pkt[i];：把包的第 i 个字节，放进档案袋的目的 MAC 里；下一次循环放 i+1……六次搬完。')
bullet('为什么不用一句搞定？因为 C 语言的数组不能整体赋值（info->mac_dst = pkt 是不合法的），只能一个字节一个字节地搬。这是初学者常踩的知识点。')
bullet('info->mac_src[i] = pkt[i + 6];：源 MAC 从第 6 个字节开始——因为前面 0～5 已经属于目的 MAC 了。这个 +6 就是「跳过 6 个字节」的意思。')
bullet('info->ethertype = rd16(pkt + 12);：类型字段在第 12 个字节，占 2 个字节——用第 4.3 节的小工具 rd16 把它读成一个数字。注意这里的 pkt + 12：指针加法，表示「从开头往后挪 12 个字节的位置」，不是「数值加 12」。')

note('观察一下注释里的一个巧妙之处：搬运顺序是把「目的 MAC 放在 0～5、源 MAC 放在 6～11」——和网络包里的实际顺序完全一致（前面讲过以太网头是「目的 MAC 在前」）。')

h2('4.9 parse_packet（三）：判断类型，剥掉第一层')

code('    if (info->ethertype != 0x0800) {\n'
     '        return 1;\n'
     '    }\n'
     '\n'
     '    const unsigned char *p = pkt + 14;\n'
     '    unsigned int plen = len - 14;')

bullet('if (info->ethertype != 0x0800) return 1;：如果类型字段不是 0x0800（不是 IPv4，比如是 ARP 包），后面的解析就没有意义了——把已解析的以太网部分保存好，返回 1 表示「解析到此为止，算成功」。打印函数看到档案袋里 has_ipv4 = 0，会打印「ARP（暂未解析）」这类说明。')
bullet('const unsigned char *p = pkt + 14;：重头戏——「剥皮」。前面 14 字节已经解析完了，从第 14 个字节开始才是「里面的东西」。新指针 p 专门指向里层数据的开头。')
bullet('unsigned int plen = len - 14;：里层还剩多少字节——总长度减去已经剥掉的 14 字节。')

para('这个「剥一层 → 指针向后挪一段 → 长度对应减一段」的手法，就是网络分层解析的全部套路。后面读 IP 头、读 TCP 头，每一次都重复这个动作。')

h2('4.10 parse_packet（四）：IPv4 头逐字段')

code('    if (plen < 20) {\n'
     '        info->note = "IPv4 头部不完整";\n'
     '        return 1;\n'
     '    }\n'
     '    unsigned int version = p[0] >> 4;\n'
     '    unsigned int ihl = (p[0] & 0x0F) * 4;\n'
     '    unsigned int frag = rd16(p + 6) & 0x1FFF;\n'
     '\n'
     '    if (version != 4) {\n'
     '        info->note = "IPv4 版本号异常";\n'
     '        return 1;\n'
     '    }\n'
     '    if (ihl < 20 || plen < ihl) {\n'
     '        info->note = "IPv4 首部长度异常";\n'
     '        return 1;\n'
     '    }')

bullet('if (plen < 20)：又是边界检查。IPv4 头至少 20 字节，不够就记一句备注「IPv4 头部不完整」再返回——注意这次不是完全失败（以太网部分还留着呢），所以返回 1，备注会告诉打印函数发生了什么。')
bullet('p[0] >> 4：把第 0 个字节「向右移 4 位」。IPv4 头的第一个字节藏着两个 4 位的小数字：高 4 位是版本号、低 4 位是首部长度。右移 4 位 = 把高 4 位挪到最低位，就得到版本号（应该是 4）。')
bullet('(p[0] & 0x0F) * 4：& 0x0F（00001111）只保留低 4 位，得到首部长度字段。这个字段的单位是「4 字节」——所以要乘 4 换算成字节数。20 字节的标准头在这里存的值就是 5（5 × 4 = 20）。')
bullet('rd16(p + 6) & 0x1FFF：第 6 个字节起的 2 个字节是「分片信息」，但其中只有低 13 位是「分片偏移」，高 3 位是别的标志。& 0x1FFF（13 个 1）把不关心的 3 位清零，只留下偏移值。偏移为 0 表示「这是第一个分片（或者根本没分片）」。')
bullet('两个 if 检查异常：版本不是 4 就备注「版本号异常」；首部长度小于 20、或者比整包剩余长度还大，就备注「首部长度异常」。所有异常都温柔地记录下来，绝不硬闯。')

para('然后是把字段搬进档案袋：')
code('    for (i = 0; i < 4; i++) {\n'
     '        info->ip_src[i] = p[i + 12];\n'
     '        info->ip_dst[i] = p[i + 16];\n'
     '    }\n'
     '    info->ttl = p[8];\n'
     '    info->proto = p[9];\n'
     '    info->has_ipv4 = 1;')
bullet('又见小循环搬运：源 IP 在 IPv4 头的第 12～15 字节，目的 IP 在第 16～19 字节，各搬 4 个字节。')
bullet('ttl = p[8]：第 8 字节，一个字节就够（0~255）。proto = p[9]：第 9 字节，协议号。')
bullet('info->has_ipv4 = 1;：全部搬完后，把「开关」打开——从这一行起，档案袋里的 IP 字段就是有效的了。这就是「开关 + 数据」模式的用法。')

h2('4.11 parse_packet（五）：分片检查与传输层分发')

code('    if (frag != 0) {\n'
     '        info->note = "这是分片的后续片，不含传输层头部，跳过端口解析";\n'
     '        return 1;\n'
     '    }\n'
     '\n'
     '    const unsigned char *transport = p + ihl;\n'
     '    unsigned int tlen = plen - ihl;')

para('分片是 IPv4 的一个特性：一个大包可以被切成几块分别传输（比如视频流的大数据块）。规则是：只有第一块带着 TCP/UDP 头，后面的块只有纯数据。如果这不是第一个分片（frag != 0 说明它的偏移不为零），强行按 TCP 解析就会读到一堆垃圾数字——所以记录一条备注「跳过端口解析」然后返回。这就是「不懂的不装懂」的工程态度。')

bullet('transport = p + ihl：传输层的起点——在 IP 头之后，而 IP 头的实际长度就是 ihl（还记得它 ×4 换算成字节了吧）。所以指针往后挪 ihl 个字节。')
bullet('tlen = plen - ihl：传输层还剩下的字节数。')

para('最后是「分发」——按协议号把活儿交给对应的解析分支：')
code('    if (info->proto == 6) {                    /* TCP */\n'
     '        if (tlen < 20) {\n'
     '            info->note = "TCP 头部不完整";\n'
     '            return 1;\n'
     '        }\n'
     '        info->sport = rd16(transport);\n'
     '        info->dport = rd16(transport + 2);\n'
     '        info->tcp_seq = rd32(transport + 4);\n'
     '        info->tcp_flags = transport[13];\n'
     '        info->has_ports = 1;\n'
     '    } else if (info->proto == 17) {            /* UDP */\n'
     '        ...（同样套路：检查 8 字节、读端口、读长度、开开关）\n'
     '    } else if (info->proto == 1) {             /* ICMP */\n'
     '        ...（检查 4 字节、读类型和代码）\n'
     '    }\n'
     '    return 1;\n'
     '}')

bullet('TCP 分支：再查一次边界（TCP 头至少 20 字节），然后用 rd16 读源端口（前 2 字节）、rd16 读目的端口（第 2 字节起）、rd32 读序列号（第 4 字节起 4 个）、transport[13] 直接取第 13 字节（标志位就在那）。最后 has_ports = 1 打开端口开关。')
bullet('UDP 分支：套路一模一样，只是「至少 8 字节」、字段位置不同（端口一样在前 4 字节、长度在第 4 字节起）。')
bullet('ICMP 分支：只需要前两个字节——transport[0] 是类型（8 = ping 请求）、transport[1] 是代码。ICMP 没有端口，所以不开端口开关。')
bullet('最后的 return 1;：所有分支跑完，报告「解析成功」。注意每个提前返回的异常分支也都是 return 1（带着写着原因的 note），只有「连以太网头都不完整」才 return 0——区分「整体失败」和「部分成功但带备注」。')

h2('4.12 小结：parse_packet 教给我们的三件事')

para('回头看不长的 90 行代码，它其实浓缩了三个受用很久的原则：')
bullet('分层剥皮：每读一层，指针往后挪「这层的长度」，剩余长度相应减少——网络解析、文件解析全是这个套路。')
bullet('先验后用：每一层动手之前先检查「剩下的字节够不够读我要的字段」，不够就优雅退出。永远不要把外部数据当诚实的——这是防崩溃、防安全漏洞的第一道门。')
bullet('开关 + 数据：用一个 has_xxx 布尔值和一组数据字段配套，表示「这组数据有没有解析出来」。解析类程序的经典模式。')

para('parse_packet 结束后，包就被完整「翻译」进了档案袋。接下来轮到两位「读者」——打印函数和统计函数——分别把档案袋变成屏幕上的文字和排行榜。')
