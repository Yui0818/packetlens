/*
 * pcaptool —— 命令行网络抓包分析工具
 * 第一阶段（最小 demo）：读取一个 pcap 文件，打印每个包的长度和时间戳。
 *
 * 这个程序是我们整个项目的起点。它做的事情非常简单：
 *   1. 打开一个 pcap 文件（pcap 是网络抓包的标准文件格式）
 *   2. 一个一个地读出里面的网络包
 *   3. 把每个包的长度、接收时间打印到屏幕上
 *   4. 最后统计一共多少个包、总共多少流量
 *
 * 看不懂没关系，我会在下方每一行都给注释。先把它跑起来，感受一下。
 */

/* #include 是"把头文件引进来"。头文件里放了别人已经写好的函数声明，
 * 我们才能直接调用。 */
#include <stdio.h>       /* printf / fprintf：向屏幕打印文字 */
#include <pcap/pcap.h>   /* libpcap：全世界通用的抓包库。里面的函数能读 pcap 文件、能抓网卡 */

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
     * 我们现在先拿到它，后面阶段会用上。 */
    int linktype = pcap_datalink(handle);

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
