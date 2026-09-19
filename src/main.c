/*
 * pcaptool —— 命令行网络抓包分析工具
 * 第一阶段（v0.1）：读取一个 pcap 文件，打印每个包的长度和时间戳。
 * 第二阶段（v0.2）：把每个包逐层"拆开"解析——以太网 → IPv4 → TCP/UDP/ICMP，
 *                  打印源/目的地址、协议、端口、TCP 标志位等信息。
 *
 * 这个程序是我们整个项目的起点，它做的事情：
 *   1. 打开一个 pcap 文件（pcap 是网络抓包的标准文件格式）
 *   2. 一个一个地读出里面的网络包
 *   3. 把每个包的长度、接收时间打印出来，并逐层解析协议头（v0.2 新增）
 *   4. 最后统计一共多少个包、总共多少流量
 *
 * 看不懂没关系，我会在下方每一行都给注释。先把它跑起来，感受一下。
 */

/* #include 是"把头文件引进来"。头文件里放了别人已经写好的函数声明，
 * 我们才能直接调用。 */
#include <stdio.h>       /* printf / fprintf：向屏幕打印文字 */
#include <pcap/pcap.h>   /* libpcap：全世界通用的抓包库。里面的函数能读 pcap 文件、能抓网卡 */

/* ============================================================
 * v0.2 新增：协议解析的"小工具箱"
 * 下面这些函数都在 main 之前定义好，main 里直接调用。
 * ============================================================ */

/* rd16 = read 2 bytes：从内存里读 2 个字节，拼成一个数字。
 * 为什么要手工拼？——网络协议规定多字节数字用"大端"（高位在前）传输，
 * 而我们的电脑（x86）是"小端"（低位在前），直接强转会读反，所以手工拼最保险。
 * "<< 8" 就是把一个字节挪到高位去（相当于乘以 256）。 */
static unsigned int rd16(const unsigned char *p) {
    return ((unsigned int)p[0] << 8) | p[1];
}

/* rd32 = read 4 bytes：一次读 4 个字节（比如 TCP 序列号就是 4 字节字段）。
 * "|" 是"按位或"，把四段拼成一个完整的数。 */
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

/* 把 IPv4 头里的"协议号"翻译成名字。 */
static const char *proto_name(unsigned int proto) {
    switch (proto) {
        case 6:  return "TCP";
        case 17: return "UDP";
        case 1:  return "ICMP";
        default: return "其它";
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

/* 解析 ICMP 头前 4 个字节：类型 + 代码。
 * ping 的"回显请求"type=8，"回显应答"type=0。 */
static void dissect_icmp(const unsigned char *p, unsigned int len) {
    if (len < 4) {
        printf("    ICMP    头部不完整（只有 %u 字节）\n", len);
        return;
    }
    unsigned int type = p[0];
    printf("    ICMP    类型=%u", type);
    if (type == 8)      printf("（回显请求 / ping）");
    else if (type == 0) printf("（回显应答 / ping 回复）");
    printf("  代码=%u\n", p[1]);
}

/* 解析 TCP 头：源端口(2) 目的端口(2) 序列号(4) ... 标志位在第 13 个字节。 */
static void dissect_tcp(const unsigned char *p, unsigned int len) {
    if (len < 20) {
        printf("    TCP     头部不完整（只有 %u 字节）\n", len);
        return;
    }
    printf("    TCP     源端口=%u  目的端口=%u  序列号=%u  标志=",
           rd16(p), rd16(p + 2), rd32(p + 4));
    print_tcp_flags(p[13]);
    printf("\n");
}

/* 解析 UDP 头（固定 8 字节）：源端口 目的端口 长度 校验和。 */
static void dissect_udp(const unsigned char *p, unsigned int len) {
    if (len < 8) {
        printf("    UDP     头部不完整（只有 %u 字节）\n", len);
        return;
    }
    printf("    UDP     源端口=%u  目的端口=%u  长度=%u\n",
           rd16(p), rd16(p + 2), rd16(p + 4));
}

/* 解析 IPv4 头。各字段的位置（从 IPv4 头起点数）：
 *   p+0    版本号(高4位) + 首部长度(低4位，单位是 4 字节)
 *   p+8    TTL（还能被路由器转发几跳）
 *   p+9    协议号（6=TCP 17=UDP 1=ICMP）
 *   p+12   源 IP(4 字节)   p+16  目的 IP(4 字节) */
static void dissect_ipv4(const unsigned char *p, unsigned int len) {
    if (len < 20) {
        printf("    IPv4    头部不完整（只有 %u 字节）\n", len);
        return;
    }
    unsigned int version = p[0] >> 4;         /* 高 4 位挪到低位，就是版本号 */
    unsigned int ihl = (p[0] & 0x0F) * 4;     /* 首部长度（单位 4 字节）→ 字节数 */
    unsigned int ttl = p[8];
    unsigned int proto = p[9];
    unsigned int frag = rd16(p + 6) & 0x1FFF; /* 分片偏移：非 0 = 不是第一个分片 */

    if (version != 4) {
        printf("    IPv4    版本号异常（%u），跳过\n", version);
        return;
    }
    if (ihl < 20 || len < ihl) {
        printf("    IPv4    首部长度异常，跳过\n");
        return;
    }

    printf("    IPv4    源=");
    print_ipv4_addr(p + 12);
    printf("  目的=");
    print_ipv4_addr(p + 16);
    printf("  协议=%s(%u)  TTL=%u\n", proto_name(proto), proto, ttl);

    /* 非首片分片里没有传输层头，强行解析会读到垃圾数据，直接跳过。 */
    if (frag != 0) {
        printf("    （这是分片的后续片，不含传输层头部，跳过端口解析）\n");
        return;
    }

    /* 传输层从哪里开始？——IPv4 头之后，即 p + ihl。
     * 还剩多少字节？——len - ihl。把这两个值交给下一层函数。 */
    const unsigned char *transport = p + ihl;
    unsigned int tlen = len - ihl;
    switch (proto) {
        case 6:  dissect_tcp(transport, tlen);  break;
        case 17: dissect_udp(transport, tlen);  break;
        case 1:  dissect_icmp(transport, tlen); break;
        default: printf("    （协议 %u 暂未解析）\n", proto); break;
    }
}

/* 解析整个包：从最外层的以太网头开始，一层一层往里剥。
 * 以太网头固定 14 字节：目的MAC(6) 源MAC(6) 类型(2)。 */
static void dissect_packet(const unsigned char *pkt, unsigned int len) {
    if (len < 14) {
        printf("    包太短（%u 字节），连以太网头都不完整。\n", len);
        return;
    }

    unsigned int ethertype = rd16(pkt + 12);   /* 最后 2 个字节 = 上层协议类型 */
    printf("    以太网  源=");
    print_mac(pkt + 6);
    printf("  目的=");
    print_mac(pkt);
    printf("  类型=%s(0x%04x)\n",
           ethertype == 0x0800 ? "IPv4" :
           ethertype == 0x0806 ? "ARP"  :
           ethertype == 0x86DD ? "IPv6" : "未知",
           ethertype);

    /* 剥掉 14 字节的以太网头，剩下的交给对应的上层协议去解析。 */
    const unsigned char *payload = pkt + 14;
    unsigned int plen = len - 14;

    if (ethertype == 0x0800) {
        dissect_ipv4(payload, plen);           /* 0x0800 = IPv4 */
    } else if (ethertype == 0x0806) {
        printf("    ARP（地址解析协议，本阶段暂未解析）\n");
    } else if (ethertype == 0x86DD) {
        printf("    IPv6（本阶段暂未解析）\n");
    }
}

/* main 是程序的入口。argc 是"命令行参数的个数"，argv 是"这些参数的内容"。
 * 比如运行  ./pcaptool xxx.pcap 时：
 *   argc = 2
 *   argv[0] = "./pcaptool"   （程序自己）
 *   argv[1] = "xxx.pcap"     （第一个参数，即要分析的文件） */
int main(int argc, char *argv[]) {

    /* 如果用户一个文件参数都没给（argc < 2），先把用法告诉他，然后退出。
     * fprintf(stderr, ...) 是"打印到错误输出"，临时错误信息都用它。 */
    if (argc < 2) {
        fprintf(stderr, "用法: %s <pcap文件>\n", argv[0]);
        return 1;   /* 返回非 0 表示程序"失败退出了" */
    }

    /* PCAP_ERRBUF_SIZE 是 libpcap 定义好的，一个错误信息缓冲区的固定大小。
     * errbuf 用来存放"万一打开文件失败了，错误原因是什么"。 */
    char errbuf[PCAP_ERRBUF_SIZE];

    /* pcap_open_offline：打开一个"离线"的 pcap 文件（而不是去抓活动的网卡）。
     * 返回一个 pcap_t*（可以理解成"这个文件的句柄"）。
     * 如果打不开，返回 NULL，并把原因写到 errbuf 里。 */
    pcap_t *handle = pcap_open_offline(argv[1], errbuf);
    if (handle == NULL) {
        fprintf(stderr, "打不开文件 %s : %s\n", argv[1], errbuf);
        return 1;
    }

    /* pcap_datalink：返回这个文件的"链路层协议类型"。
     * 简单说，就是告诉大家这是以太网(Ethernet)还是别的。
     * v0.1 里先把它存着；v0.2 起它派上用场了——本程序按"以太网"格式解析包，
     * 所以先确认文件是不是以太网，不是的话提醒一句（解析结果可能不准）。
     * DLT_EN10MB 是 libpcap 定义的"以太网"常量（值为 1）。 */
    int linktype = pcap_datalink(handle);
    if (linktype != DLT_EN10MB) {
        fprintf(stderr, "警告：该文件的链路层类型不是以太网（%d），解析结果可能不准。\n", linktype);
    }

    /* 两个指针：header 会指向"这个包的信息"（长度、时间），
     * packet 会指向"这个包的原始字节数据"。 */
    struct pcap_pkthdr *header;
    const u_char *packet;

    /* 统计用的累加变量。 */
    long long total = 0;                 /* 一共读了多少个包 */
    unsigned long long bytes = 0;        /* 这些包合起来多少字节 */

    /* while(1) 是"永远循环"，要靠里面的 break 来跳出。 */
    while (1) {
        /* pcap_next_ex：读"下一个"包。
         * 返回值有三种：
         *   1   = 成功读到一个包
         *   -1  = 出错
         *   -2  = 文件到末尾了（读完啦） */
        int ret = pcap_next_ex(handle, &header, &packet);
        if (ret == 1) {
            total++;
            bytes += header->len;   /* header->len 是这个包的长度 */

            /* header->ts 是时间戳：tv_sec 是"秒"，tv_usec 是"微秒"。 */
            printf("#%lld  时间=%lu.%06lu  长度=%u\n",
                   total,
                   (unsigned long)header->ts.tv_sec,
                   (unsigned long)header->ts.tv_usec,
                   header->len);

            /* v0.2 新增：把这个包逐层拆开解析（以太网 → IPv4 → TCP/UDP/ICMP）。 */
            dissect_packet(packet, header->len);
        } else if (ret == -1) {
            fprintf(stderr, "读包出错。\n");
            break;
        } else if (ret == -2) {
            printf("--- 文件读取完毕 ---\n");
            break;
        }
    }

    /* 汇总报告。 */
    printf("共 %lld 个包，总流量 %llu 字节\n", total, bytes);

    /* 用完一定要关掉文件，释放资源。 */
    pcap_close(handle);
    return 0;   /* 0 表示"成功结束" */
}
