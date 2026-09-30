# -*- coding: utf-8 -*-
"""第 4 章（下·一）：main.c 逐行详解——print_packet 与统计系统。"""

from docbuild import *

h2('4.13 print_packet：把档案袋打印成人类读的样子')

para('parse_packet 负责「读」，print_packet 负责「说」。它的任务是读一份 PacketInfo，按固定格式打印到你屏幕上。完整代码分四段讲。')

h3('第一段：以太网层永远先打印')
code('static void print_packet(const PacketInfo *info) {\n'
     '    printf("    以太网  源=");\n'
     '    print_mac(info->mac_src);\n'
     '    printf("  目的=");\n'
     '    print_mac(info->mac_dst);\n'
     '    printf("  类型=%s(0x%04x)\\n", ethertype_name(info->ethertype), info->ethertype);')

bullet('参数是 const PacketInfo *info——只读地看一眼档案袋，不改动。')
bullet('注意这几行的排版手法：printf 打印「以太网 源=」这几个字 → 调用 print_mac 打印 MAC 本身 → 再 printf「 目的=」……为什么分成好几段？因为地址的打印格式封装在 print_mac 里，printf 没法直接把「函数的结果」插进字符串中间，只能拆开轮流打印。')
bullet('最后一行 %s(0x%04x)：%s 填一个字符串（ethertype_name 返回的「IPv4」），%04x 填一个至少 4 位的十六进制数字（0x0800 这种）。两个值对应后面两个参数，顺序一一对应。')

h3('第二段：三个提前退出（guard clause 风格）')
code('    if (info->ethertype != 0x0800) {\n'
     '        if (info->ethertype == 0x0806) {\n'
     '            printf("    ARP（地址解析协议，本阶段暂未解析）\\n");\n'
     '        } else if (info->ethertype == 0x86DD) {\n'
     '            printf("    IPv6（本阶段暂未解析）\\n");\n'
     '        }\n'
     '        return;\n'
     '    }\n'
     '\n'
     '    if (!info->has_ipv4) {\n'
     '        if (info->note) printf("    （%s）\\n", info->note);\n'
     '        return;\n'
     '    }')

bullet('第一个提前退出：不是 IPv4（ARP / IPv6 / 未知），打印一句说明就 return（函数到此结束）。这种「先处理特殊情况，直接退出，别往下走」的写法叫 guard clause（守卫子句），比一层套一层的 if 清爽得多。')
bullet('第二个提前退出：是 IPv4 但没解析成功（has_ipv4 = 0，比如被截断了）。这时如果有备注（note 不是 NULL）就把备注打印出来——「（IPv4 头部不完整）」这种。')
bullet('if (info->note) 的写法：C 语言里「指针非空」可以直接当「真」来用，等价于 if (info->note != NULL)。这是 C 的惯用法。')

h3('第三段：IPv4 层与备注')
code('    printf("    IPv4    源=");\n'
     '    print_ipv4_addr(info->ip_src);\n'
     '    printf("  目的=");\n'
     '    print_ipv4_addr(info->ip_dst);\n'
     '    printf("  协议=%s(%u)  TTL=%u\\n", proto_name(info->proto), info->proto, info->ttl);\n'
     '\n'
     '    if (info->note) {\n'
     '        printf("    （%s）\\n", info->note);\n'
     '        return;\n'
     '    }')
bullet('又是「分段打印」：源 IP、目的 IP、协议名、协议号、TTL 拼成一行。%u 填十进制无符号整数。')
bullet('如果这条信息流有备注（比如「这是分片的后续片……」），打印备注并 return——后面没有端口数据可讲了。')

h3('第四段：按协议分支，打印细节')
code('    if (info->proto == 6) {\n'
     '        printf("    TCP     源端口=%u  目的端口=%u  序列号=%u  标志=",\n'
     '               info->sport, info->dport, info->tcp_seq);\n'
     '        print_tcp_flags((unsigned char)info->tcp_flags);\n'
     '        printf("\\n");\n'
     '    } else if (info->proto == 17) {\n'
     '        printf("    UDP     源端口=%u  目的端口=%u  长度=%u\\n",\n'
     '               info->sport, info->dport, info->udp_len);\n'
     '    } else if (info->proto == 1) {\n'
     '        printf("    ICMP    类型=%u", info->icmp_type);\n'
     '        if (info->icmp_type == 8)      printf("（回显请求 / ping）");\n'
     '        else if (info->icmp_type == 0) printf("（回显应答 / ping 回复）");\n'
     '        printf("  代码=%u\\n", info->icmp_code);\n'
     '    } else {\n'
     '        printf("    （协议 %u 暂未解析）\\n", info->proto);\n'
     '    }\n'
     '}')

bullet('TCP 分支：打印端口和序列号，然后调用 print_tcp_flags 打印标志，最后自己补一个换行——因为标志是另一个函数打印的，换行得由这个函数收尾。')
bullet('(unsigned char)info->tcp_flags：类型转换。tcp_flags 存的是 unsigned int，但 print_tcp_flags 的门口写着「我要 unsigned char」。强制转换一下，告诉编译器「放心收」。')
bullet('UDP 分支：多了个「长度」字段（UDP 头里自带）。')
bullet('ICMP 分支：先打印类型数字，然后按类型补一句解释（8 = 请求、0 = 应答），最后打印代码。')
bullet('最后的 else：协议号不是 6/17/1 的（比如 GRE 隧道），打印「暂未解析」——程序永远有兜底。')

note('打印格式小秘密：你会注意到每层开头都有 4 个空格缩进、层次分明（以太网 → IPv4 → TCP）。这是刻意设计的，让输出看起来像一棵「协议树」，一眼看出层级关系。')

h2('4.14 统计系统（一）：两张「计数器表」')

para('从这一节开始进入 v0.3 的统计功能。先看基础设施——两张表，记录「每个 IP 出现几次」「每个端口出现几次」：')

code('#define MAX_ENTRIES 128\n'
     '\n'
     'typedef struct {\n'
     '    unsigned int key;\n'
     '    long long    count;\n'
     '} Counter;\n'
     '\n'
     'typedef struct {\n'
     '    Counter items[MAX_ENTRIES];\n'
     '    int     n;\n'
     '} CounterTable;')

bullet('#define MAX_ENTRIES 128：预处理器定义——在编译前，代码里所有 MAX_ENTRIES 都会被替换成 128。这是 C 定义常量的传统方式（比到处写 128 好维护）。')
bullet('Counter：一行计数器——key（是谁，比如某个 IP 的档案号）+ count（出现次数）。long long 是能存很大的整数类型（64 位）。')
bullet('CounterTable：整张表 = items（固定 128 行的数组）+ n（当前用了几行）。')

para('然后是两张「全局表」和一堆全局计数器：')
code('static CounterTable ip_table;\n'
     'static CounterTable port_table;\n'
     '\n'
     'static long long tcp_pkts = 0,  tcp_bytes = 0;\n'
     'static long long udp_pkts = 0,  udp_bytes = 0;\n'
     'static long long icmp_pkts = 0, icmp_bytes = 0;\n'
     '\n'
     'static long long total = 0;\n'
     'static unsigned long long bytes = 0;\n'
     'static long long shown = 0;\n'
     'static unsigned long long shown_bytes = 0;\n'
     'static long long filtered = 0;')

para('这些叫「全局变量」：定义在所有函数外面，程序运行期间一直活着，所有函数都能直接读写。')
bullet('为什么统计用全局变量？图方便——统计天生是「全程序一份」的：每个包处理时 +1、最后统一汇报，用全局最直接，不用层层传参数。')
bullet('代价是什么？全局变量多了以后，「谁改了它」很难追踪。等程序更大时，更好的做法是把这些装进一个结构体传来传去。这里是个取舍：教学项目优先「看得懂」。')
bullet('每个变量的含义：tcp_pkts/tcp_bytes 等 = 各协议的包数与字节数；total/bytes = 读入总数；shown/shown_bytes = 「显示出来的」数量（过滤会让它小于 total）；filtered = 被过滤掉的数量。')

h2('4.15 统计系统（二）：counter_add 与 counter_sort')

code('static void counter_add(CounterTable *t, unsigned int key) {\n'
     '    int i;\n'
     '    for (i = 0; i < t->n; i++) {\n'
     '        if (t->items[i].key == key) {\n'
     '            t->items[i].count++;\n'
     '            return;\n'
     '        }\n'
     '    }\n'
     '    if (t->n < MAX_ENTRIES) {\n'
     '        t->items[t->n].key = key;\n'
     '        t->items[t->n].count = 1;\n'
     '        t->n++;\n'
     '    }\n'
     '}')

para('counter_add 的活儿：往表里记一笔「key 出现了」。逻辑三句话说完：')
bullet('第一段 for：从头到尾找一遍，看这个 key 在不在表里。找到了就 count++（次数加一），立刻 return（干完收工）。')
bullet('第二段 if：没找到（循环跑完都没 return）→ 新增一行：把 key 写进去、count 从 1 开始、表的行数 n 加一。')
bullet('为什么不用哈希表？数据量小（几个到几十个 key）时，这种「线性查找」又快又简单；等包里出现百万个不同 IP 时再换哈希表也不迟——「先跑起来，再优化」是工程常态。')
bullet('t->items[i] 这种写法：t 是指向表的指针，t->items 等价于 (*t).items——「顺着指针找到表，再取出 items」。箭头 -> 就是干这个的。')
bullet('表满（n 到 128）时的行为：默默丢弃。注释里写明了「样例数据不可能满；真实场景要扩容或换哈希表」——知道自己的边界在哪，并写下来，是好代码的标志。')

code('static void counter_sort(CounterTable *t) {\n'
     '    int i, j;\n'
     '    for (i = 0; i < t->n - 1; i++) {\n'
     '        int maxj = i;\n'
     '        for (j = i + 1; j < t->n; j++) {\n'
     '            if (t->items[j].count > t->items[maxj].count) {\n'
     '                maxj = j;\n'
     '            }\n'
     '        }\n'
     '        if (maxj != i) {\n'
     '            Counter tmp = t->items[i];\n'
     '            t->items[i] = t->items[maxj];\n'
     '            t->items[maxj] = tmp;\n'
     '        }\n'
     '    }\n'
     '}')

para('counter_sort 是「选择排序」——把表按 count 从大到小排好。外层循环 i 表示「当前位置」；内层循环在剩下的行里找「最大的那一行」的下标 maxj；找到后就把它换到位置 i。')
bullet('maxj = i 的初始值：先假设当前行就是最大的，然后一个个和后面比较，发现更大的就更新 maxj。')
bullet('交换三行（tmp 中转）：如果最大行不在当前位置，就把两者互换。交换两个变量需要一个「中转站」，这是排序算法的经典动作：tmp = a; a = b; b = tmp;')
bullet('为什么整个结构体能一句赋值（t->items[i] = t->items[maxj]）？因为 Counter 是结构体，C 语言允许结构体整体赋值——这和前面「数组不能整体赋值」形成对比，别搞混。')

h2('4.16 统计系统（三）：stats_update 与"收发都算"的设计')

code('static void stats_update(const PacketInfo *info, unsigned int full_len) {\n'
     '    if (!info->has_ipv4) {\n'
     '        return;\n'
     '    }\n'
     '\n'
     '    counter_add(&ip_table, ip_to_key(info->ip_src));\n'
     '    counter_add(&ip_table, ip_to_key(info->ip_dst));\n'
     '\n'
     '    if (info->has_ports) {\n'
     '        counter_add(&port_table, info->sport);\n'
     '        counter_add(&port_table, info->dport);\n'
     '    }\n'
     '\n'
     '    if (info->proto == 6) {\n'
     '        tcp_pkts++;\n'
     '        tcp_bytes += full_len;\n'
     '    } else if (info->proto == 17) {\n'
     '        udp_pkts++;\n'
     '        udp_bytes += full_len;\n'
     '    } else if (info->proto == 1) {\n'
     '        icmp_pkts++;\n'
     '        icmp_bytes += full_len;\n'
     '    }\n'
     '}')

bullet('参数 full_len：整个包的长度（连以太网头一起算）。为什么不用 PacketInfo 里现成的？因为档案袋里没有「总长」这个字段——它是从外面传进来的。统计「流量占比」用的是整包长度，这样百分比加起来才是 100%。')
bullet('开头的守卫：不是 IPv4 的包（ARP 之类）不统计，直接返回。')
bullet('「收发都算」的设计：源 IP 和目的 IP 都记一笔——所以一段对话里，两个 IP 各自的次数都会涨。端口同理（源端口、目的端口都记）。这就是输出里那句「（收发都算）」的由来。这样统计出来的是「谁最活跃」，而不是「谁只是被访问得多」。')
bullet('协议计数：TCP 的包就让 tcp_pkts 加一、字节数累加 full_len；UDP、ICMP 同理。')

h2('4.17 统计系统（四）：emit_stats——同一份要写两份的通道设计')

para('统计的最后一步是把结果打印出来。你可能注意到函数名不叫 print_stats 而叫 emit_stats——这是 v0.6 的一个小改造，看签名就懂：')
code('static void emit_stats(FILE *out, unsigned long long total_bytes) {')
bullet('第一个参数 FILE *out 是「往哪儿写」：屏幕（stdout）还是文件，由调用者决定。emit 是「发射、输出」的意思，比 print 更中性——它不一定打到屏幕上。')
bullet('函数体里所有的 printf 都换成了 fprintf(out, ...)——用法一模一样，只是第一个参数指明目的地。')

code('    if (total_bytes == 0) {\n'
     '        return;\n'
     '    }\n'
     '    fprintf(out, "\\n====== 协议统计 ======\\n");\n'
     '    if (tcp_pkts > 0)\n'
     '        fprintf(out, "TCP      %lld 个包   %lld 字节（%.1f%%）\\n",\n'
     '                tcp_pkts, tcp_bytes, 100.0 * tcp_bytes / total_bytes);')
bullet('防除零：如果总字节是 0（空文件或有极端过滤），直接返回——避免除以 0（除零在 C 里是灾难）。')
bullet('每条协议一行，都有 if (xxx_pkts > 0) 守卫：没出现过的协议不显示，避免「TCP 0 个包」这样的废话。')
bullet('%.1f%%：打印一个小数，保留 1 位；%% 表示「一个真的百分号字符」（因为单个 % 会被当成格式符）。')
bullet('100.0 * tcp_bytes / total_bytes：这是第 4.15 节强调过的整数除法坑的正式应用——100 写成 100.0，整个式子就是小数运算，47.9 这种小数才不会被截断。')
bullet('格式串里的 %lld：填 long long 类型的数字（大整数）。类型和字母必须一一对应，写错会打出天文数字——这是 C 常见的低级 bug。')

para('Top 榜的部分：')
code('    if (ip_table.n > 0) {\n'
     '        fprintf(out, "\\n====== Top IP（收发都算）======\\n");\n'
     '        counter_sort(&ip_table);\n'
     '        int limit = ip_table.n < 5 ? ip_table.n : 5;\n'
     '        int i;\n'
     '        for (i = 0; i < limit; i++) {\n'
     '            print_ip_from_key(out, ip_table.items[i].key);\n'
     '            fprintf(out, "    %lld 次\\n", ip_table.items[i].count);\n'
     '        }\n'
     '    }')
bullet('先排序（counter_sort），再从前往后取——取几条？limit = 「表的行数和 5 里小的那个」：表里不到 5 条就全看，超过 5 条只看前 5。三元表达式再次出场。')
bullet('循环里先打印 IP（print_ip_from_key 现在也接受 out，写成指示的目的地），再打印次数。')
bullet('端口榜的代码完全同构，只是打印的是端口数字。')

note('设计的品味：一份数据、两种去向（屏幕/文件）——关键就是把「处理逻辑」和「写去哪里」解耦。这个思路在软件工程里叫「关注点分离」，你已经在用真代码实践它了。')

h2('4.18 统计系统（五）：write_report——第一次「写文件」')

code('static void write_report(const char *path) {\n'
     '    FILE *f = fopen(path, "w");\n'
     '    if (f == NULL) {\n'
     '        fprintf(stderr, "报告文件打不开: %s\\n", path);\n'
     '        return;\n'
     '    }\n'
     '    fprintf(f, "pcaptool 分析报告\\n");\n'
     '    fprintf(f, "================\\n\\n");\n'
     '    fprintf(f, "共 %lld 个包，总流量 %llu 字节\\n", total, bytes);\n'
     '    if (filtered > 0) {\n'
     '        fprintf(f, "已过滤掉 %lld 个包（统计只算显示的 %lld 个）\\n", filtered, shown);\n'
     '    }\n'
     '    emit_stats(f, shown_bytes);\n'
     '    fclose(f);\n'
     '    printf("报告已写入: %s\\n", path);\n'
     '}')

bullet('FILE *f = fopen(path, "w")：打开文件准备写入。"w" 模式 = 没有就新建、有就清空重写。返回值是一个「文件句柄」（FILE 指针），以后对文件的一切操作都用它。')
bullet('if (f == NULL)：打开失败（比如路径不存在、没权限）时 fopen 返回空指针——必须检查，不然下面一操作就崩溃。报错信息写到 stderr（错误流），这是「报错去错误通道」的惯例。')
bullet('fprintf(f, ...)：写内容进文件。用起来和 printf 一模一样，只是第一个参数是文件句柄。')
bullet('emit_stats(f, shown_bytes)：把整个统计报告复用进来——同一份逻辑，这次写进文件。')
bullet('fclose(f)：关闭文件。为什么必须关？①操作系统对打开的文件数量有限制；②要写入的内容可能还在「缓冲区」里没真正落盘，fclose 会把它冲出去——不关文件，报告可能不完整。')
bullet('最后一行 printf 是写给人看的确认信息，打在屏幕上（不是文件里）。')

para('到这里，main.c 的「功能函数」全部讲完了。剩下的是把这些零件组装起来的最后两块：过滤系统和主函数 main。请看下一节。')
