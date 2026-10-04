/*
 * PacketLens（网镜）—— 命令行网络抓包分析工具
 * 第一阶段（v0.1）：读取一个 pcap 文件，打印每个包的长度和时间戳。
 * 第二阶段（v0.2）：把每个包逐层"拆开"解析——以太网 → IPv4 → TCP/UDP/ICMP。
 * 第三阶段（v0.3）：统计——按协议算流量占比、Top IP、Top 端口排名。
 *                  为此做了一次重构：先把解析结果整理成一个结构体（PacketInfo），
 *                  再分别交给"打印"和"统计"去用（而不是边解析边打印）。
 * 第四阶段（v0.4）：过滤表达式——只显示关心的包（比如 tcp port 80）。
 * 第五阶段（v0.5）：实时抓网卡（live 模式）——和读文件共用同一套解析管线。
 * 第六阶段（v0.6）：导出分析报告（--report 文件名）——同一份统计写到文件。
 *
 * 这个程序是我们整个项目的起点，它做的事情：
 *   1. 打开一个 pcap 文件（pcap 是网络抓包的标准文件格式）
 *   2. 一个一个地读出里面的网络包
 *   3. 把每个包的长度、接收时间打印出来，并逐层解析协议头（v0.2）
 *   4. 统计协议流量占比和 Top IP / 端口（v0.3）
 *
 * 看不懂没关系，我会在下方每一行都给注释。先把它跑起来，感受一下。
 */

/* #include 是"把头文件引进来"。头文件里放了别人已经写好的函数声明，
 * 我们才能直接调用。 */
#include <stdio.h>       /* printf / fprintf：向屏幕打印文字 */
#include <stdlib.h>      /* atoi：把命令行里的文字数字转成整数 */
#include <string.h>      /* strcmp：比较两个字符串是不是一样 */
#include <pcap/pcap.h>   /* libpcap：全世界通用的抓包库。里面的函数能读 pcap 文件、能抓网卡 */

/* ============================================================
 * 基础小工具：读字节、打印地址
 * ============================================================ */

/* rd16 = read 2 bytes：从内存里读 2 个字节，拼成一个数字。
 * 为什么要手工拼？——网络协议规定多字节数字用"大端"（高位在前）传输，
 * 而我们的电脑（x86）是"小端"（低位在前），直接强转会读反，所以手工拼最保险。
 * "<< 8" 就是把一个字节挪到高位去（相当于乘以 256）。 */
static unsigned int rd16(const unsigned char *p) {
    return ((unsigned int)p[0] << 8) | p[1];
}

/* rd32 = read 4 bytes：一次读 4 个字节（比如 TCP 序列号、IP 地址）。 */
static unsigned int rd32(const unsigned char *p) {
    return ((unsigned int)p[0] << 24) | ((unsigned int)p[1] << 16) |
           ((unsigned int)p[2] << 8)  | (unsigned int)p[3];
}

/* 打印 MAC 地址：6 个字节写成 aa:bb:cc:dd:ee:ff 的习惯格式。
 * %02x = 用十六进制打印，不足 2 位前面补 0。 */
static void print_mac(const unsigned char *m) {
    printf("%02x:%02x:%02x:%02x:%02x:%02x", m[0], m[1], m[2], m[3], m[4], m[5]);
}

/* 打印 IPv4 地址：4 个字节写成"点分十进制"（192.168.1.1）。
 * 其实 IP 地址在磁盘上就是 4 个 0~255 的数字，只是大家习惯这么写。 */
static void print_ipv4_addr(const unsigned char *a) {
    printf("%u.%u.%u.%u", a[0], a[1], a[2], a[3]);
}

/* 把 4 个字节的 IP 压缩成一个数字，方便当作"计数表的钥匙"（key）。
 * 例如 192.168.1.109 → 0xC0A8016D。以后建表、查表都用这个数。 */
static unsigned int ip_to_key(const unsigned char *a) {
    return ((unsigned int)a[0] << 24) | ((unsigned int)a[1] << 16) |
           ((unsigned int)a[2] << 8)  | a[3];
}

/* 反过来：把一个数字"钥匙"还原成 IP 打印出来（写去哪由 out 决定，屏幕/文件都行）。
 * >> 24 是"往右挪 24 位"，& 0xFF 是"只取最低 8 位"，这样一段一段取出来。 */
static void print_ip_from_key(FILE *out, unsigned int key) {
    fprintf(out, "%u.%u.%u.%u",
            (key >> 24) & 0xFF, (key >> 16) & 0xFF, (key >> 8) & 0xFF, key & 0xFF);
}

/* 把 IPv4 头里的"协议号"翻译成名字。 */
static const char *proto_name(unsigned int proto) {
    switch (proto) {
        case 6:  return "TCP";
        case 17: return "UDP";
        case 1:  return "ICMP";
        default: return "其它";
    }
}

/* 把以太网类型字段翻译成名字。 */
static const char *ethertype_name(unsigned int t) {
    switch (t) {
        case 0x0800: return "IPv4";
        case 0x0806: return "ARP";
        case 0x86DD: return "IPv6";
        default:     return "未知";
    }
}

/* 把 TCP 标志位（1 个字节、8 个比特）翻译成人话，如 SYN / SYN+ACK / PSH+ACK。
 * 每个比特是一个开关：0x02=SYN(建连接) 0x10=ACK(确认) 0x08=PSH(立即交付)
 *                   0x01=FIN(挂断) 0x04=RST(复位) 0x20=URG(紧急)
 * "f & 0x02" 是"按位与"：那一位是 1，结果就非 0，说明这个标志开着。 */
static void print_tcp_flags(unsigned char f) {
    int first = 1;   /* 控制 "+" 加号：第一个标志前面不加 */
    if (f & 0x02) { printf("SYN"); first = 0; }
    if (f & 0x01) { printf(first ? "FIN" : "+FIN"); first = 0; }
    if (f & 0x04) { printf(first ? "RST" : "+RST"); first = 0; }
    if (f & 0x08) { printf(first ? "PSH" : "+PSH"); first = 0; }
    if (f & 0x10) { printf(first ? "ACK" : "+ACK"); first = 0; }
    if (f & 0x20) { printf(first ? "URG" : "+URG"); first = 0; }
    if (first)    { printf("（无）"); }   /* 一个标志都没开 */
}

/* ============================================================
 * v0.3 重构：解析结果结构体 + 解析 / 打印分离
 * ============================================================ */

/* PacketInfo：一个包"解析出来"的全部信息。
 * 重构的原因：v0.2 是"边解析边打印"，但统计（还有以后的过滤）也需要这些信息，
 * 总不能让它再去解析一遍。所以统一先解析进这个结构体，谁需要谁来读。 */
typedef struct {
    /* 以太网层 */
    unsigned char mac_src[6];
    unsigned char mac_dst[6];
    unsigned int  ethertype;       /* 0x0800=IPv4 ... */

    /* IPv4 层 */
    int           has_ipv4;        /* 1 = 成功解析出 IPv4 头 */
    unsigned char ip_src[4];
    unsigned char ip_dst[4];
    unsigned int  proto;           /* 6=TCP 17=UDP 1=ICMP */
    unsigned int  ttl;

    /* 传输层 */
    int           has_ports;       /* 1 = 解析出了 TCP/UDP 端口 */
    unsigned int  sport, dport;
    unsigned int  udp_len;         /* UDP 头里的长度字段 */
    unsigned int  tcp_seq;
    unsigned int  tcp_flags;
    unsigned int  icmp_type, icmp_code;

    /* 给打印用的一句话备注（比如"头部不完整"），没有就是 NULL */
    const char   *note;
} PacketInfo;

/* 解析一个包，把结果填进 info。
 * 返回 1 = 解析成功（可能只有部分层），返回 0 = 连以太网头都不完整。 */
static int parse_packet(const unsigned char *pkt, unsigned int len, PacketInfo *info) {
    /* 先给所有字段一个"没有"的默认值，防止用到没初始化的垃圾数据。 */
    info->has_ipv4 = 0;
    info->has_ports = 0;
    info->note = NULL;

    /* 以太网头固定 14 字节：目的MAC(6) 源MAC(6) 类型(2)。
     * 这里用一个循环把 6 个字节搬进结构体——数组不能整体赋值，只能一个个搬。 */
    if (len < 14) {
        return 0;
    }
    int i;
    for (i = 0; i < 6; i++) {
        info->mac_dst[i] = pkt[i];
        info->mac_src[i] = pkt[i + 6];
    }
    info->ethertype = rd16(pkt + 12);

    if (info->ethertype != 0x0800) {
        return 1;   /* 不是 IPv4（比如 ARP/IPv6），到此为止，打印时说明即可 */
    }

    /* 剥掉 14 字节以太网头，进入 IPv4 层。 */
    const unsigned char *p = pkt + 14;
    unsigned int plen = len - 14;

    if (plen < 20) {
        info->note = "IPv4 头部不完整";
        return 1;
    }
    unsigned int version = p[0] >> 4;         /* 高 4 位 = 版本号 */
    unsigned int ihl = (p[0] & 0x0F) * 4;     /* 低 4 位 = 首部长度（单位 4 字节） */
    unsigned int frag = rd16(p + 6) & 0x1FFF; /* 分片偏移：非 0 = 不是第一个分片 */

    if (version != 4) {
        info->note = "IPv4 版本号异常";
        return 1;
    }
    if (ihl < 20 || plen < ihl) {
        info->note = "IPv4 首部长度异常";
        return 1;
    }

    for (i = 0; i < 4; i++) {
        info->ip_src[i] = p[i + 12];
        info->ip_dst[i] = p[i + 16];
    }
    info->ttl = p[8];
    info->proto = p[9];
    info->has_ipv4 = 1;

    /* 非首片分片里没有传输层头，强行解析会读到垃圾数据，直接跳过。 */
    if (frag != 0) {
        info->note = "这是分片的后续片，不含传输层头部，跳过端口解析";
        return 1;
    }

    /* 传输层从哪里开始？——IPv4 头之后，即 p + ihl。
     * 还剩多少字节？——plen - ihl。 */
    const unsigned char *transport = p + ihl;
    unsigned int tlen = plen - ihl;

    if (info->proto == 6) {                    /* TCP */
        if (tlen < 20) {
            info->note = "TCP 头部不完整";
            return 1;
        }
        info->sport = rd16(transport);
        info->dport = rd16(transport + 2);
        info->tcp_seq = rd32(transport + 4);
        info->tcp_flags = transport[13];
        info->has_ports = 1;
    } else if (info->proto == 17) {            /* UDP */
        if (tlen < 8) {
            info->note = "UDP 头部不完整";
            return 1;
        }
        info->sport = rd16(transport);
        info->dport = rd16(transport + 2);
        info->udp_len = rd16(transport + 4);
        info->has_ports = 1;
    } else if (info->proto == 1) {             /* ICMP */
        if (tlen < 4) {
            info->note = "ICMP 头部不完整";
            return 1;
        }
        info->icmp_type = transport[0];
        info->icmp_code = transport[1];
    }
    return 1;
}

/* 把一个解析好的包打印出来（格式和 v0.2 一样，只是现在读的是结构体）。 */
static void print_packet(const PacketInfo *info) {
    printf("    以太网  源=");
    print_mac(info->mac_src);
    printf("  目的=");
    print_mac(info->mac_dst);
    printf("  类型=%s(0x%04x)\n", ethertype_name(info->ethertype), info->ethertype);

    if (info->ethertype != 0x0800) {
        if (info->ethertype == 0x0806) {
            printf("    ARP（地址解析协议，本阶段暂未解析）\n");
        } else if (info->ethertype == 0x86DD) {
            printf("    IPv6（本阶段暂未解析）\n");
        }
        return;
    }

    if (!info->has_ipv4) {
        if (info->note) printf("    （%s）\n", info->note);
        return;
    }

    printf("    IPv4    源=");
    print_ipv4_addr(info->ip_src);
    printf("  目的=");
    print_ipv4_addr(info->ip_dst);
    printf("  协议=%s(%u)  TTL=%u\n", proto_name(info->proto), info->proto, info->ttl);

    if (info->note) {
        printf("    （%s）\n", info->note);
        return;
    }

    if (info->proto == 6) {
        printf("    TCP     源端口=%u  目的端口=%u  序列号=%u  标志=",
               info->sport, info->dport, info->tcp_seq);
        print_tcp_flags((unsigned char)info->tcp_flags);
        printf("\n");
    } else if (info->proto == 17) {
        printf("    UDP     源端口=%u  目的端口=%u  长度=%u\n",
               info->sport, info->dport, info->udp_len);
    } else if (info->proto == 1) {
        printf("    ICMP    类型=%u", info->icmp_type);
        if (info->icmp_type == 8)      printf("（回显请求 / ping）");
        else if (info->icmp_type == 0) printf("（回显应答 / ping 回复）");
        printf("  代码=%u\n", info->icmp_code);
    } else {
        printf("    （协议 %u 暂未解析）\n", info->proto);
    }
}

/* ============================================================
 * v0.3 新增：统计
 * ============================================================ */

/* 计数器表：把"某个 key 出现了几次"记下来。
 * 用最简单的做法：一个小数组 + 线性查找。数据量小的时候足够快，
 * 以后数据量大再换成哈希表（那是以后的事儿）。
 * 说明：表用了"全局变量"，所有函数都能直接读写——小程序图方便，
 * 等代码更大时更好的做法是当参数传来传去（放到"重构"话题里讲）。 */
#define MAX_ENTRIES 128

typedef struct {
    unsigned int key;
    long long    count;
} Counter;

typedef struct {
    Counter items[MAX_ENTRIES];
    int     n;                      /* 现在存了几项 */
} CounterTable;

static CounterTable ip_table;       /* 每个 IP 出现次数（收发都算） */
static CounterTable port_table;     /* 每个端口出现次数（收发都算） */

/* 协议计数器：包数 + 字节数。 */
static long long tcp_pkts = 0,  tcp_bytes = 0;
static long long udp_pkts = 0,  udp_bytes = 0;
static long long icmp_pkts = 0, icmp_bytes = 0;

/* 运行总账（离线读文件 / 在线抓网卡两个模式共用同一套）。 */
static long long total = 0;                 /* 一共读/抓了多少个包 */
static unsigned long long bytes = 0;        /* 这些包合起来多少字节 */
static long long shown = 0;                 /* 其中显示出来的（通过过滤的） */
static unsigned long long shown_bytes = 0;  /* 显示出来的包的字节数（统计只算这部分） */
static long long filtered = 0;              /* 被过滤掉的包数 */

/* 给某个 key 的次数 +1；表里没有这个 key 就先插入一行。 */
static void counter_add(CounterTable *t, unsigned int key) {
    int i;
    for (i = 0; i < t->n; i++) {
        if (t->items[i].key == key) {
            t->items[i].count++;
            return;
        }
    }
    if (t->n < MAX_ENTRIES) {
        t->items[t->n].key = key;
        t->items[t->n].count = 1;
        t->n++;
    }
    /* 表满就丢弃（样例数据不可能满；真实场景要扩容或换哈希表） */
}

/* 按次数从大到小排序。用"选择排序"：简单直观，数据小的时候够用。 */
static void counter_sort(CounterTable *t) {
    int i, j;
    for (i = 0; i < t->n - 1; i++) {
        int maxj = i;
        for (j = i + 1; j < t->n; j++) {
            if (t->items[j].count > t->items[maxj].count) {
                maxj = j;
            }
        }
        if (maxj != i) {
            Counter tmp = t->items[i];
            t->items[i] = t->items[maxj];
            t->items[maxj] = tmp;
        }
    }
}

/* 每解析完一个包，把它的信息记进统计里。
 * full_len 是整个包的长度（包含以太网头），统计"流量占比"用的就是它。 */
static void stats_update(const PacketInfo *info, unsigned int full_len) {
    if (!info->has_ipv4) {
        return;   /* 只统计 IPv4 包 */
    }

    counter_add(&ip_table, ip_to_key(info->ip_src));
    counter_add(&ip_table, ip_to_key(info->ip_dst));

    if (info->has_ports) {
        counter_add(&port_table, info->sport);
        counter_add(&port_table, info->dport);
    }

    if (info->proto == 6) {
        tcp_pkts++;
        tcp_bytes += full_len;
    } else if (info->proto == 17) {
        udp_pkts++;
        udp_bytes += full_len;
    } else if (info->proto == 1) {
        icmp_pkts++;
        icmp_bytes += full_len;
    }
}

/* 输出统计报告。写去哪由 out 决定——屏幕（stdout）或报告文件都走这一份逻辑。
 * 注意 "100.0 *" 里的 .0：如果写成 100 * bytes / total，C 语言会做"整数除法"，
 * 小数部分全被丢掉（比如 0.479 会变成 0）；写成 100.0 就会变成小数运算。 */
static void emit_stats(FILE *out, unsigned long long total_bytes) {
    if (total_bytes == 0) {
        return;
    }

    fprintf(out, "\n====== 协议统计 ======\n");
    if (tcp_pkts > 0)
        fprintf(out, "TCP      %lld 个包   %lld 字节（%.1f%%）\n",
                tcp_pkts, tcp_bytes, 100.0 * tcp_bytes / total_bytes);
    if (udp_pkts > 0)
        fprintf(out, "UDP      %lld 个包   %lld 字节（%.1f%%）\n",
                udp_pkts, udp_bytes, 100.0 * udp_bytes / total_bytes);
    if (icmp_pkts > 0)
        fprintf(out, "ICMP     %lld 个包   %lld 字节（%.1f%%）\n",
                icmp_pkts, icmp_bytes, 100.0 * icmp_bytes / total_bytes);

    if (ip_table.n > 0) {
        fprintf(out, "\n====== Top IP（收发都算）======\n");
        counter_sort(&ip_table);
        int limit = ip_table.n < 5 ? ip_table.n : 5;   /* 最多显示前 5 名 */
        int i;
        for (i = 0; i < limit; i++) {
            print_ip_from_key(out, ip_table.items[i].key);
            fprintf(out, "    %lld 次\n", ip_table.items[i].count);
        }
    }

    if (port_table.n > 0) {
        fprintf(out, "\n====== Top 端口（收发都算）======\n");
        counter_sort(&port_table);
        int limit = port_table.n < 5 ? port_table.n : 5;
        int i;
        for (i = 0; i < limit; i++) {
            fprintf(out, "%u     %lld 次\n", port_table.items[i].key, port_table.items[i].count);
        }
    }
}

/* v0.6：把这次分析的结果写成一份文本报告。
 * fopen 的 "w" 表示"写文件"（没有就新建、有就覆盖）——和 printf 全家桶
 * 是一个用法，只是"往哪写"从屏幕换成了文件；打开的东西用完必须 fclose。 */
static void write_report(const char *path) {
    FILE *f = fopen(path, "w");
    if (f == NULL) {
        fprintf(stderr, "报告文件打不开: %s\n", path);
        return;
    }
    fprintf(f, "PacketLens 分析报告\n");
    fprintf(f, "================\n\n");
    fprintf(f, "共 %lld 个包，总流量 %llu 字节\n", total, bytes);
    if (filtered > 0) {
        fprintf(f, "已过滤掉 %lld 个包（统计只算显示的 %lld 个）\n", filtered, shown);
    }
    emit_stats(f, shown_bytes);
    fclose(f);
    printf("报告已写入: %s\n", path);
}

/* ============================================================
 * v0.4 新增：过滤器
 * ============================================================ */

/* 过滤条件：命令行里写 tcp / port 80 / host 1.2.3.4 这样的词，就是填这里。
 * 三个条件都可以不写（= 不限）；写了就必须满足。 */
typedef struct {
    int           proto;       /* 0 = 不限协议 */
    int           port;        /* 0 = 不限端口 */
    int           has_host;    /* 1 = 只显示和这个 IP 有关的包 */
    unsigned char host[4];
} Filter;

static Filter filter;          /* 全局一份，默认全是"不限" */

/* v0.6：命令行 --report 指定的报告文件名（NULL = 不写报告）。 */
static const char *report_file = NULL;

/* 把字符串 "192.168.1.1" 解析成 4 个字节。
 * sscanf 是"从字符串里按格式抠数字"的利器：%u 表示"抠一个无符号整数"。 */
static int parse_ip(const char *s, unsigned char *out) {
    unsigned int a, b, c, d;
    if (sscanf(s, "%u.%u.%u.%u", &a, &b, &c, &d) != 4) return 0;
    if (a > 255 || b > 255 || c > 255 || d > 255) return 0;
    out[0] = a;
    out[1] = b;
    out[2] = c;
    out[3] = d;
    return 1;
}

/* 解析命令行的附加参数（从第 start 个参数开始）。
 * 支持：tcp / udp / icmp；port 80；host 192.168.1.1；--report 文件名；
 * 也可以组合，如 "tcp port 80"。
 * 返回 1 = 解析成功，0 = 有看不懂的词。 */
static int parse_filter_args(int argc, char *argv[], int start) {
    int i;
    for (i = start; i < argc; i++) {
        const char *a = argv[i];
        if (strcmp(a, "tcp") == 0) {
            filter.proto = 6;
        } else if (strcmp(a, "udp") == 0) {
            filter.proto = 17;
        } else if (strcmp(a, "icmp") == 0) {
            filter.proto = 1;
        } else if (strcmp(a, "port") == 0) {
            if (++i >= argc) return 0;      /* "port" 后面必须跟数字 */
            filter.port = atoi(argv[i]);    /* atoi：把 "80" 这样的文字转成整数 80 */
            if (filter.port <= 0 || filter.port > 65535) return 0;
        } else if (strcmp(a, "host") == 0) {
            if (++i >= argc) return 0;      /* "host" 后面必须跟 IP */
            if (!parse_ip(argv[i], filter.host)) return 0;
            filter.has_host = 1;
        } else if (strcmp(a, "--report") == 0) {
            if (++i >= argc) return 0;      /* "--report" 后面必须跟文件名 */
            report_file = argv[i];
        } else {
            return 0;                       /* 不认识的词 */
        }
    }
    return 1;
}

/* 判断一个包符不符合过滤条件：三样条件有一样不满足，就返回 0（不显示）。
 * 没设的条件直接跳过。 */
static int filter_match(const PacketInfo *info) {
    if (filter.proto != 0) {
        if (!info->has_ipv4 || info->proto != (unsigned int)filter.proto) return 0;
    }
    if (filter.port != 0) {
        if (!info->has_ports) return 0;
        if (info->sport != (unsigned int)filter.port &&
            info->dport != (unsigned int)filter.port) return 0;
    }
    if (filter.has_host) {
        if (!info->has_ipv4) return 0;
        if (ip_to_key(info->ip_src) != ip_to_key(filter.host) &&
            ip_to_key(info->ip_dst) != ip_to_key(filter.host)) return 0;
    }
    return 1;
}

/* 处理一个包：编号 → 解析 → 过滤 → 打印 → 统计。
 * 离线读文件和在线抓网卡都调用这一段，保证两个模式行为完全一致。 */
static void handle_packet(const struct pcap_pkthdr *header, const unsigned char *packet) {
    total++;
    bytes += header->len;

    /* 解析 → 过滤 → 打印 → 统计（流水线）。
     * info = {0} 是"先全部清零"：保证每个字段都有确定的值，
     * 不会出现"没解析到就读到垃圾"的情况（编译器也因此不再报警告）。 */
    PacketInfo info = {0};
    int ok = parse_packet(packet, header->len, &info);

    if (ok && filter_match(&info)) {
        /* 只有"通过过滤"的包才打印。header->ts 是时间戳：
         * tv_sec 是"秒"，tv_usec 是"微秒"。编号用的是"读入的序号"，
         * 所以有过滤时编号会跳号——这正是过滤在起作用。 */
        printf("#%lld  时间=%lu.%06lu  长度=%u\n",
               total,
               (unsigned long)header->ts.tv_sec,
               (unsigned long)header->ts.tv_usec,
               header->len);
        print_packet(&info);
        stats_update(&info, header->len);
        shown++;
        shown_bytes += header->len;
    } else {
        filtered++;
    }
}

/* main 是程序的入口。argc 是"命令行参数的个数"，argv 是"这些参数的内容"。
 * 比如运行  ./packetlens xxx.pcap 时：
 *   argc = 2
 *   argv[0] = "./packetlens"   （程序自己）
 *   argv[1] = "xxx.pcap"     （第一个参数，即要分析的文件） */
int main(int argc, char *argv[]) {

    /* 如果用户一个文件参数都没给（argc < 2），先把用法告诉他，然后退出。
     * fprintf(stderr, ...) 是"打印到错误输出"，临时错误信息都用它。 */
    if (argc < 2) {
        fprintf(stderr, "用法: %s <pcap文件> [过滤表达式] [--report 文件名]\n", argv[0]);
        fprintf(stderr, "      %s live [网卡名] [数量] [过滤表达式] [--report 文件名]\n", argv[0]);
        fprintf(stderr, "过滤表达式示例: tcp / udp / icmp / port 80 / tcp port 80 / host 192.168.1.1\n");
        return 1;   /* 返回非 0 表示程序"失败退出了" */
    }

    /* v0.5：第一个参数是 "live" 就走"实时抓网卡"模式，否则按"读 pcap 文件"处理。 */
    int live_mode = strcmp(argv[1], "live") == 0;

    /* 过滤表达式在命令行里的位置：
     *   离线模式：./packetlens 文件.pcap [过滤...]          → 从 argv[2] 开始
     *   在线模式：./packetlens live [网卡] [数量] [过滤...] → 网卡、数量占了两个位置
     * 判断"数量"的小技巧：atoi 对 "tcp" 这样的文字会返回 0，
     * 所以"能转成正数"就说明用户写的是数量。 */
    int filter_start = 2;
    int live_count = 20;      /* 实时模式最多抓多少个包 */
    if (live_mode) {
        filter_start = 3;
        if (argc > 3 && atoi(argv[3]) > 0) {
            live_count = atoi(argv[3]);
            filter_start = 4;
        }
    }
    if (!parse_filter_args(argc, argv, filter_start)) {
        fprintf(stderr, "过滤表达式看不懂。支持的写法示例: tcp / udp / icmp / port 80 / tcp port 80 / host 192.168.1.1\n");
        return 1;
    }

    /* PCAP_ERRBUF_SIZE 是 libpcap 定义好的，一个错误信息缓冲区的固定大小。
     * errbuf 用来存放"万一打开失败了，错误原因是什么"。 */
    char errbuf[PCAP_ERRBUF_SIZE];

    /* 两个指针：header 会指向"这个包的信息"（长度、时间），
     * packet 会指向"这个包的原始字节数据"。 */
    struct pcap_pkthdr *header;
    const u_char *packet;

    pcap_t *handle;

    if (live_mode) {
        /* ===== v0.5：实时抓网卡 ===== */

        /* 不写网卡名就默认 "any"（监听所有网卡；也可以指定 eth0、lo 等）。 */
        const char *dev = (argc > 2) ? argv[2] : "any";

        /* pcap_open_live：实时抓包的"开幕"。四个参数：
         *   dev     网卡名
         *   65535   每个包最多抓多少字节（够装下整个包）
         *   1       混杂模式：连"不是发给本机"的包也抓（交换机"旁听"）
         *   1000    超时（毫秒）：没包最多等 1 秒就返回，程序好继续干活 */
        handle = pcap_open_live(dev, 65535, 1, 1000, errbuf);
        if (handle == NULL) {
            fprintf(stderr, "打不开网卡 %s : %s\n", dev, errbuf);
            return 1;
        }
        if (pcap_datalink(handle) != DLT_EN10MB) {
            fprintf(stderr, "警告：该网卡链路层不是以太网格式（%d），解析可能不准（可以换成 eth0 这类网口试试）。\n",
                    pcap_datalink(handle));
        }

        printf("正在监听 %s ...（最多抓 %d 个包，想提前停就按 Ctrl+C）\n", dev, live_count);

        int got = 0;
        while (got < live_count) {
            /* 在线模式的 pcap_next_ex 多了一种返回值：
             *   0 = 这段时间没等到包（超时），继续等就行。 */
            int ret = pcap_next_ex(handle, &header, &packet);
            if (ret == 1) {
                handle_packet(header, packet);
                got++;
            } else if (ret == 0) {
                continue;
            } else {
                fprintf(stderr, "抓包出错。\n");
                break;
            }
        }
        printf("--- 抓包停止（已抓 %d 个）---\n", got);

    } else {
        /* ===== 离线模式：读一个 pcap 文件 ===== */

        /* pcap_open_offline：打开一个"离线"的 pcap 文件（而不是去抓活动的网卡）。
         * 返回一个 pcap_t*（可以理解成"这个文件的句柄"）。
         * 如果打不开，返回 NULL，并把原因写到 errbuf 里。 */
        handle = pcap_open_offline(argv[1], errbuf);
        if (handle == NULL) {
            fprintf(stderr, "打不开文件 %s : %s\n", argv[1], errbuf);
            return 1;
        }

        /* pcap_datalink：返回这个文件的"链路层协议类型"。
         * 简单说，就是告诉大家这是以太网(Ethernet)还是别的。
         * v0.1 里先把它存着；v0.2 起它派上用场——用来提醒"这个文件不是以太网格式的话，
         * 解析结果可能不准"。DLT_EN10MB 是 libpcap 定义的"以太网"常量（值为 1）。 */
        int linktype = pcap_datalink(handle);
        if (linktype != DLT_EN10MB) {
            fprintf(stderr, "警告：该文件的链路层类型不是以太网（%d），解析结果可能不准。\n", linktype);
        }

        /* while(1) 是"永远循环"，要靠里面的 break 来跳出。 */
        while (1) {
            /* pcap_next_ex：读"下一个"包。
             * 返回值有三种（离线模式）：
             *   1   = 成功读到一个包
             *   -1  = 出错
             *   -2  = 文件到末尾了（读完啦） */
            int ret = pcap_next_ex(handle, &header, &packet);
            if (ret == 1) {
                handle_packet(header, packet);
            } else if (ret == -1) {
                fprintf(stderr, "读包出错。\n");
                break;
            } else if (ret == -2) {
                printf("--- 文件读取完毕 ---\n");
                break;
            }
        }
    }

    /* 汇总报告。 */
    printf("共 %lld 个包，总流量 %llu 字节\n", total, bytes);

    /* 有过滤时说明一下统计口径：只算"显示出来"的包。 */
    if (filtered > 0) {
        printf("已过滤掉 %lld 个包（统计只算显示的 %lld 个）。\n", filtered, shown);
    }

    /* v0.3：统计报告（协议占比 + Top IP + Top 端口）。 */
    emit_stats(stdout, shown_bytes);

    /* v0.6：命令行给了 --report 的话，把同样的结果写一份到文件。 */
    if (report_file != NULL) {
        write_report(report_file);
    }

    /* 用完一定要关掉文件，释放资源。 */
    pcap_close(handle);
    return 0;   /* 0 表示"成功结束" */
}
