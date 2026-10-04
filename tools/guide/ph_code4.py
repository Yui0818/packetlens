# -*- coding: utf-8 -*-
"""第 4 章（下·二）：main.c 逐行详解——过滤器、handle_packet 与 main 主函数。"""

from docbuild import *

h1('第 4 章  main.c 逐行详解（下）')

h2('4.19 过滤器（一）：Filter 结构体')

para('过滤功能（v0.4）要用最小的代码量支持「tcp / udp / icmp / port 80 / host 1.2.3.4」这些条件。设计如下：')

code('typedef struct {\n'
     '    int           proto;       /* 0 = 不限协议 */\n'
     '    int           port;        /* 0 = 不限端口 */\n'
     '    int           has_host;    /* 1 = 只显示和这个 IP 有关的包 */\n'
     '    unsigned char host[4];\n'
     '} Filter;\n'
     '\n'
     'static Filter filter;')

bullet('四个字段对应三类条件：proto（想只看哪个协议）、port（想只看哪个端口）、has_host + host（想只看和哪个 IP 有关的包）。')
bullet('「不限」用什么表示？proto/port 用 0——因为协议号 0 和端口 0 在现实里都不存在，正好拿来当「没设置」的哨兵值。host 则需要额外的开关 has_host，因为 0.0.0.0 是个「合法但罕见」的地址，光靠全零判断「有没有设置」不保险。')
bullet('static Filter filter;：全局一份。所有解析到的包都拿它来对照。没写过滤条件时，它就保持初始状态（全 0），相当于「什么都放行」。')

h2('4.20 过滤器（二）：parse_ip——把文字变成 4 个字节')

code('static int parse_ip(const char *s, unsigned char *out) {\n'
     '    unsigned int a, b, c, d;\n'
     '    if (sscanf(s, "%u.%u.%u.%u", &a, &b, &c, &d) != 4) return 0;\n'
     '    if (a > 255 || b > 255 || c > 255 || d > 255) return 0;\n'
     '    out[0] = a;\n'
     '    out[1] = b;\n'
     '    out[2] = c;\n'
     '    out[3] = d;\n'
     '    return 1;\n'
     '}')

bullet('任务：把用户在命令行敲的 "192.168.1.1" 变成 4 个字节存进 out 数组。')
bullet('sscanf：scanf 的字符串版——从一段文字里「按模板抠数字」。%u 表示「抠一个无符号整数」，四个 %u 用点隔开，对应「用点分隔的四段数字」。它返回「成功抠出了几段」，所以 != 4 就说明格式不对（比如用户写了个 1.2.3）。')
bullet('第二行范围检查：每一段必须 ≤ 255（IP 的规矩）。如果写的是 999.1.1.1，直接判错。因为类型是 unsigned（无符号），不可能小于 0，所以只检查上界。')
bullet('最后把四段数字存进 out[0..3]。注意 out 是调用者给的数组（Filter 里的 host），这个函数往里面填——又是「传指针、原地填」的模式。')
bullet('返回 0/1 表示成功失败，和 parse_packet 的约定一致。')

h2('4.21 过滤器（三）：parse_filter_args——读懂命令行')

para('用户在命令行里可能写「tcp port 80 host 1.2.3.4」这样一串词，这个函数负责把这些词逐个翻译进 filter 结构体：')

code('static int parse_filter_args(int argc, char *argv[], int start) {\n'
     '    int i;\n'
     '    for (i = start; i < argc; i++) {\n'
     '        const char *a = argv[i];\n'
     '        if (strcmp(a, "tcp") == 0) {\n'
     '            filter.proto = 6;\n'
     '        } else if (strcmp(a, "udp") == 0) {\n'
     '            filter.proto = 17;\n'
     '        } else if (strcmp(a, "icmp") == 0) {\n'
     '            filter.proto = 1;\n'
     '        } else if (strcmp(a, "port") == 0) {\n'
     '            if (++i >= argc) return 0;\n'
     '            filter.port = atoi(argv[i]);\n'
     '            if (filter.port <= 0 || filter.port > 65535) return 0;\n'
     '        } else if (strcmp(a, "host") == 0) {\n'
     '            if (++i >= argc) return 0;\n'
     '            if (!parse_ip(argv[i], filter.host)) return 0;\n'
     '            filter.has_host = 1;\n'
     '        } else if (strcmp(a, "--report") == 0) {\n'
     '            if (++i >= argc) return 0;\n'
     '            report_file = argv[i];\n'
     '        } else {\n'
     '            return 0;\n'
     '        }\n'
     '    }\n'
     '    return 1;\n'
     '}')

bullet('参数 start：从第几个参数开始读——离线模式从 argv[2] 开始，live 模式从 argv[3] 或 argv[4] 开始（因为前面的位置被文件名、网卡名占了）。同一套解析代码，两种模式复用。')
bullet('strcmp(a, "tcp") == 0：比较两段文字是否完全相同。相等时 strcmp 返回 0（是的，0 表示「相等」——第一次遇到很容易记反）。')
bullet('for 循环把所有词挨个过一遍：是 tcp/udp/icmp 就设协议；是 port 就把下一个词转成数字（atoi）存起来；是 host 就把下一个词解析成 IP；是 --report 就把下一个词记成报告文件名（v0.6 加的）。')
bullet('++i 这个小细节：读走「port」之后，马上把 i 加一，让下一次循环直接跳过「80」这个词——它已经被消费掉了。++i 的意思是「先加一，再用新值」。')
bullet('每个「需要跟一个值」的分支都先检查 ++i >= argc——万一用户只写了「port」没跟数字呢？不能越界去读不存在的参数，直接返回 0 报错。')
bullet('port 的范围检查 0~65535：端口是 16 位无符号数，超了就是写错了。')
bullet('最后的 else return 0：遇到完全不认识的词（比如把 port 打成 pot）就整个判失败，程序会打印用法示例。宁可报错，不要「猜」用户的意思。')

h2('4.22 过滤器（四）：filter_match——三条军规')

code('static int filter_match(const PacketInfo *info) {\n'
     '    if (filter.proto != 0) {\n'
     '        if (!info->has_ipv4 || info->proto != (unsigned int)filter.proto) return 0;\n'
     '    }\n'
     '    if (filter.port != 0) {\n'
     '        if (!info->has_ports) return 0;\n'
     '        if (info->sport != (unsigned int)filter.port &&\n'
     '            info->dport != (unsigned int)filter.port) return 0;\n'
     '    }\n'
     '    if (filter.has_host) {\n'
     '        if (!info->has_ipv4) return 0;\n'
     '        if (ip_to_key(info->ip_src) != ip_to_key(filter.host) &&\n'
     '            ip_to_key(info->ip_dst) != ip_to_key(filter.host)) return 0;\n'
     '    }\n'
     '    return 1;\n'
     '}')

para('每个包都要过这一关：三道检查全过（返回 1）才显示，任何一道没过（返回 0）就被过滤。')
bullet('第一道（协议）：只有当用户写了协议条件时才生效。注意先检查 has_ipv4——如果这个包压根不是 IPv4，它的 proto 字段没有意义，直接判「不符合」。')
bullet('第二道（端口）：同样先看条件是否设置。包必须解析出了端口（has_ports），而且源端口、目的端口里「至少有一个」等于用户要的端口——所以用 && 连接两个「不等于」：两个都不等，才判不符合。')
bullet('第三道（主机）：把源 IP 和目的 IP 都换算成档案号，和用户的 host 比——「收发都算」在这里的体现：不管你是发出方还是接收方，只要涉及这个 IP 就放行。')
bullet('三道都过 → return 1。没有任何条件时（用户没写过滤），三道检查全部被条件守护跳过，直接返回 1——所有包放行。逻辑天然自洽。')

h2('4.23 handle_packet：两种模式共用的「流水线」')

para('v0.5 加实时抓包时，把「处理一个包」的流程抽成了 handle_packet——不管是读文件还是抓网卡，拿到一个包都走同一条流水线：')

code('static void handle_packet(const struct pcap_pkthdr *header, const unsigned char *packet) {\n'
     '    total++;\n'
     '    bytes += header->len;\n'
     '\n'
     '    PacketInfo info = {0};\n'
     '    int ok = parse_packet(packet, header->len, &info);\n'
     '\n'
     '    if (ok && filter_match(&info)) {\n'
     '        printf("#%lld  时间=%lu.%06lu  长度=%u\\n",\n'
     '               total,\n'
     '               (unsigned long)header->ts.tv_sec,\n'
     '               (unsigned long)header->ts.tv_usec,\n'
     '               header->len);\n'
     '        print_packet(&info);\n'
     '        stats_update(&info, header->len);\n'
     '        shown++;\n'
     '        shown_bytes += header->len;\n'
     '    } else {\n'
     '        filtered++;\n'
     '    }\n'
     '}')

bullet('参数 header 是 libpcap 给的「包信息」（时间戳、长度），packet 是包的字节。两者配套，来自 pcap_next_ex。')
bullet('total++ / bytes += header->len：无论后面显示与否，先把「读入总数」的账记上。')
bullet('PacketInfo info = {0};：整个档案袋先清零。那个 {0} 是「全部字段初始化为 0」的写法——v0.3 时编译器曾警告「字段可能未初始化」，这就是当时的修复（第 4.15 节讲过原因，再看一眼就懂了）。')
bullet('int ok = parse_packet(...)：先解析。')
bullet('if (ok && filter_match(&info))：两个条件都过才显示——①解析没整体失败（ok）；②过滤器放行（filter_match）。&& 是「并且」，左边为假就不看右边（短路求值）。')
bullet('显示四件事：①打印包编号行——#编号、时间戳（%lu.%06lu 拼成「秒.微秒」，%06lu 表示微秒补足 6 位）；②print_packet 打印层级细节；③stats_update 记入统计；④shown / shown_bytes 计数。')
bullet('else filtered++：没通过的包不算数，只记一笔「被过滤」。注意——统计只记「显示出来的包」，这是 v0.4 定下的口径。')
bullet('编号用什么？total（读入序号）——所以过滤时编号会跳号，#1 #2 #4 中间的 3 去哪了，一眼可见：被过滤了。')

h2('4.24 main（一）：用法提示与参数解析')

para('终于到了 main——程序的入口。它先处理「用户到底想干嘛」，再决定走哪条路。')

code('int main(int argc, char *argv[]) {\n'
     '    if (argc < 2) {\n'
     '        fprintf(stderr, "用法: %s <pcap文件> [过滤表达式] [--report 文件名]\\n", argv[0]);\n'
     '        fprintf(stderr, "      %s live [网卡名] [数量] [过滤表达式] [--report 文件名]\\n", argv[0]);\n'
     '        fprintf(stderr, "过滤表达式示例: tcp / udp / icmp / port 80 / tcp port 80 / host 192.168.1.1\\n");\n'
     '        return 1;\n'
     '    }')

bullet('argc / argv 复习：运行 ./packetlens a b 时，argc = 3（数一数：程序自己 + a + b），argv[0] = "./packetlens"，argv[1] = "a"，argv[2] = "b"。')
bullet('argc < 2 说明用户只敲了程序名——什么信息都没给，打印用法。用法里的 %s 填 argv[0]（程序名），所以不管你把程序改名成什么，提示都自动正确。')
bullet('返回 1（非 0）表示「失败退出」——这是命令行程序的约定：0 = 成功，非 0 = 出错。')

code('    int live_mode = strcmp(argv[1], "live") == 0;\n'
     '\n'
     '    int filter_start = 2;\n'
     '    int live_count = 20;\n'
     '    if (live_mode) {\n'
     '        filter_start = 3;\n'
     '        if (argc > 3 && atoi(argv[3]) > 0) {\n'
     '            live_count = atoi(argv[3]);\n'
     '            filter_start = 4;\n'
     '        }\n'
     '    }\n'
     '    if (!parse_filter_args(argc, argv, filter_start)) {\n'
     '        fprintf(stderr, "过滤表达式看不懂。支持的写法示例: ...\\n");\n'
     '        return 1;\n'
     '    }')

bullet('live_mode：第一个参数是不是「live」这个词？是就进实时模式，否则按读文件。strcmp 返回 0 表示相等，== 0 成立时 live_mode 就是 1。')
bullet('filter_start：过滤条件从第几个参数开始读？读文件时前面只有「文件名」一个占位，所以从 2 开始；live 模式前面可能有「网卡名」「数量」两个占位，所以先假设从 3 开始。')
bullet('那句话的小魔术：atoi 把文字转成数字，遇到「tcp」这种非数字文字会返回 0。所以 if (atoi(argv[3]) > 0) 的效果就是「如果第 3 个参数是个正数，说明用户写的是抓包数量」——同时 live_count 被设成这个数，filter_start 挪到 4。一行代码同时完成「判断」和「取值」。')
bullet('最后统一调用 parse_filter_args（从 filter_start 开始）——离线、在线两种模式共用同一套过滤解析。解析失败就打印提示并退出。')

h2('4.25 main（二）：两条路——实时抓包 vs 读文件')

para('接下来是整段「岔路口」：')
code('    char errbuf[PCAP_ERRBUF_SIZE];\n'
     '    struct pcap_pkthdr *header;\n'
     '    const u_char *packet;\n'
     '    pcap_t *handle;')
bullet('errbuf：错误信息的「箩筐」——libpcap 出错时会把原因写进这个字符数组。PCAP_ERRBUF_SIZE 是 libpcap 规定的大小（够装下任何错误消息）。')
bullet('header / packet：两个「出参」——等下循环调用 pcap_next_ex 时，libpcap 会把「当前包的信息」和「当前包的字节」分别塞进这两个指针指向的地方。')
bullet('handle：抓包会话的句柄——不管是打开文件还是打开网卡，都得到这么一个「遥控器」，之后所有操作都通过它。')

para('先看 live 这条路：')
code('    if (live_mode) {\n'
     '        const char *dev = (argc > 2) ? argv[2] : "any";\n'
     '        handle = pcap_open_live(dev, 65535, 1, 1000, errbuf);\n'
     '        if (handle == NULL) {\n'
     '            fprintf(stderr, "打不开网卡 %s : %s\\n", dev, errbuf);\n'
     '            return 1;\n'
     '        }\n'
     '        ...\n'
     '        printf("正在监听 %s ...（最多抓 %d 个包，想提前停就按 Ctrl+C）\\n", dev, live_count);\n'
     '\n'
     '        int got = 0;\n'
     '        while (got < live_count) {\n'
     '            int ret = pcap_next_ex(handle, &header, &packet);\n'
     '            if (ret == 1) {\n'
     '                handle_packet(header, packet);\n'
     '                got++;\n'
     '            } else if (ret == 0) {\n'
     '                continue;\n'
     '            } else {\n'
     '                fprintf(stderr, "抓包出错。\\n");\n'
     '                break;\n'
     '            }\n'
     '        }\n'
     '        printf("--- 抓包停止（已抓 %d 个）---\\n", got);')

bullet('dev 取名：用户写了网卡名就用它（argv[2]），没写就用 "any"（监听所有网卡）。三元表达式再就业。')
bullet('pcap_open_live(dev, 65535, 1, 1000, errbuf)：打开网卡。四个数分别是「最大抓包长度 65535 字节」「混杂模式 1（连不是发给本机的也抓）」「超时 1000 毫秒」「错误筐」。')
bullet('打不开就报错退出——和打开文件一样的套路（NULL 检查 + errbuf 里的原因）。')
bullet('抓包循环：got 记录已抓到几个，满了 live_count 就收工。pcap_next_ex 在实时模式下多了一种返回值 0 = 「这段时间没包」，这时 continue 继续等（不计数）——这就是实时模式和读文件最大的区别。')
bullet('ret == 1 抓到包 → 交给 handle_packet（和读文件模式同一个函数！）→ got++。其他值（-1）报错退出。')
bullet('结束打印「已抓 N 个」——注意 N 是实际抓到的，用户 Ctrl+C 提前停时 N 可能小于预期，如实报告。')

para('再看读文件这条路：')
code('    } else {\n'
     '        handle = pcap_open_offline(argv[1], errbuf);\n'
     '        if (handle == NULL) {\n'
     '            fprintf(stderr, "打不开文件 %s : %s\\n", argv[1], errbuf);\n'
     '            return 1;\n'
     '        }\n'
     '\n'
     '        int linktype = pcap_datalink(handle);\n'
     '        if (linktype != DLT_EN10MB) {\n'
     '            fprintf(stderr, "警告：该文件的链路层类型不是以太网（%d）...\\n", linktype);\n'
     '        }\n'
     '\n'
     '        while (1) {\n'
     '            int ret = pcap_next_ex(handle, &header, &packet);\n'
     '            if (ret == 1) {\n'
     '                handle_packet(header, packet);\n'
     '            } else if (ret == -1) {\n'
     '                fprintf(stderr, "读包出错。\\n");\n'
     '                break;\n'
     '            } else if (ret == -2) {\n'
     '                printf("--- 文件读取完毕 ---\\n");\n'
     '                break;\n'
     '            }\n'
     '        }\n'
     '    }')

bullet('pcap_open_offline：打开离线 pcap 文件——和 open_live 是对应的一组函数。打不开就报错退出。')
bullet('pcap_datalink + DLT_EN10MB：检查这个文件的链路层类型是不是「以太网」（本程序只懂以太网格式）。不是的话给个警告继续——尽力而为。这个检查就是 v0.1 里那个「暂时没用上的 linktype 变量」在 v0.2 真正派上的用场。')
bullet('读文件的循环：没有数量上限，一直读到文件尾。三种返回值：1 = 读到包（处理）；-1 = 出错（报告、跳出）；-2 = 文件读完（打印「读取完毕」、跳出）。')
bullet('对照看两条路：结构几乎一模一样，唯一的差别在「返回值含义」和「循环退出条件」——这就是把公共部分抽成 handle_packet 的好处：差异被压缩到最少，一眼就能对比。')

h2('4.26 main（三）：收尾——汇总、统计与报告')

code('    printf("共 %lld 个包，总流量 %llu 字节\\n", total, bytes);\n'
     '\n'
     '    if (filtered > 0) {\n'
     '        printf("已过滤掉 %lld 个包（统计只算显示的 %lld 个）。\\n", filtered, shown);\n'
     '    }\n'
     '\n'
     '    emit_stats(stdout, shown_bytes);\n'
     '\n'
     '    if (report_file != NULL) {\n'
     '        write_report(report_file);\n'
     '    }\n'
     '\n'
     '    pcap_close(handle);\n'
     '    return 0;\n'
     '}')

bullet('第一行：无论哪种模式，最后都打印总账。%llu 对应 unsigned long long 类型（大无符号整数）。')
bullet('过滤说明行只有真的过滤过才打（filtered > 0）——没过滤时不啰嗦。')
bullet('emit_stats(stdout, shown_bytes)：打到屏幕上。第一个参数是 stdout（标准输出 = 屏幕）——同一个函数，换个参数去向就变了。')
bullet('report_file != NULL：用户在命令行写了 --report 才写报告。write_report 内部自己负责打开文件、写、关闭、报错。')
bullet('pcap_close(handle)：关闭抓包会话，释放资源——打开的东西都要关：文件句柄、抓包句柄，一个都不能漏。')
bullet('return 0：告诉操作系统「一切正常」。整个 main 到此结束，程序的生命周期结束。')

h2('4.27 第 4 章总结：一张图记住整个程序')

para('把全章串起来，main.c 的运行骨架就是这张图：')

image('tools/assets/d06_pipeline.png', '图 4-1：main.c 的数据流水线——两种输入模式共用同一套处理')
code('main 开始\n'
     '  ├─ 没参数？        → 打印用法，退出\n'
     '  ├─ 解析过滤条件    → parse_filter_args（内部用 strcmp / atoi / parse_ip）\n'
     '  ├─ 选路：\n'
     '  │    ├─ live 模式  → pcap_open_live 打开网卡\n'
     '  │    └─ 文件模式   → pcap_open_offline 打开文件\n'
     '  └─ 每个包都走同一条流水线 handle_packet：\n'
     '        parse_packet   （拆包 → PacketInfo 档案袋）\n'
     '           ↓\n'
     '        filter_match   （过滤器放行吗？）\n'
     '           ↓ 放行\n'
     '        print_packet   （打印层级细节）\n'
     '           ↓\n'
     '        stats_update   （记入统计）\n'
     '  └─ 收尾：\n'
     '        emit_stats     （统计报告 → 屏幕）\n'
     '        write_report   （可选：同样的报告 → 文件）\n'
     '        pcap_close     （关掉句柄）')

para('这张图值得抄在笔记本上。面试被要求「讲讲这个项目的架构」时，把这条流水线讲一遍，再挑 parse_packet 的「边界检查」和 emit_stats 的「一个函数两种去向」展开——已经是非常扎实的回答了。')

para('main.c 逐行讲解到此结束。下一章看项目里的其他文件——它们保证了这个程序「能编译、能被测试、能被发布」。')
