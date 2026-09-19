# pcaptool

一个用 **C 语言** 写成的命令行网络抓包 / 分析工具（轻量版 tcpdump / Wireshark）。

> 学习 & 教学项目：从零开始，一行一行用 C 实现网络协议解析。

## 这是什么

`pcaptool` 能读取网络抓包文件（`.pcap` 格式），逐个解析其中的网络数据包，
并做统计。它基于业界通用抓包库 **libpcap**（Wireshark / tcpdump 底层同款）。

```
$ ./pcaptool samples/sample.pcap
#1  时间=1700000000.000100  长度=54
    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)
    IPv4    源=192.168.1.109  目的=93.184.216.34  协议=TCP(6)  TTL=64
    TCP     源端口=54321  目的端口=80  序列号=100  标志=SYN
#2  时间=1700000000.000200  长度=54
    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)
    IPv4    源=93.184.216.34  目的=192.168.1.109  协议=TCP(6)  TTL=64
    TCP     源端口=80  目的端口=54321  序列号=1000  标志=SYN+ACK
#3  时间=1700000000.000300  长度=79
    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)
    IPv4    源=93.184.216.34  目的=192.168.1.109  协议=UDP(17)  TTL=64
    UDP     源端口=53  目的端口=50000  长度=45
#4  时间=1700000000.000400  长度=101
    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)
    IPv4    源=192.168.1.109  目的=93.184.216.34  协议=TCP(6)  TTL=64
    TCP     源端口=54321  目的端口=80  序列号=200  标志=PSH+ACK
#5  时间=1700000000.000500  长度=74
    以太网  源=00:11:22:33:44:55  目的=aa:bb:cc:dd:ee:ff  类型=IPv4(0x0800)
    IPv4    源=192.168.1.109  目的=192.168.1.1  协议=ICMP(1)  TTL=64
    ICMP    类型=8（回显请求 / ping）  代码=0
#6  时间=1700000000.000600  长度=74
    以太网  源=aa:bb:cc:dd:ee:ff  目的=00:11:22:33:44:55  类型=IPv4(0x0800)
    IPv4    源=192.168.1.1  目的=192.168.1.109  协议=ICMP(1)  TTL=64
    ICMP    类型=0（回显应答 / ping 回复）  代码=0
--- 文件读取完毕 ---
共 6 个包，总流量 436 字节
```

## 功能（持续开发中）

- [x] 读取 `.pcap` 文件
- [x] 遍历并打印每个包的长度 / 时间戳
- [x] 解析以太网 / IPv4 / TCP / UDP / ICMP 头（v0.2）
- [ ] 按协议统计流量占比
- [ ] 过滤表达式（如 `tcp port 80`）
- [ ] Top IP / Top 端口 排名
- [ ] 实时网卡抓包
- [ ] 导出报告

## 为什么做这个

- **学习底层网络**：通过亲手解析二进制协议，理解网络每一层的工作方式。
- **C 语言的实战**：位操作、内存管理、字节序、数据结构，是 C 的最佳训练场。
- **解决真实问题**：网络工程师 / 开发者排查网络问题时，抓包工具是刚需。

## 构建

依赖：Linux + GCC + libpcap 开发库。

```bash
# Ubuntu / Debian
sudo apt install libpcap-dev

# 编译
make

# 运行
./pcaptool samples/sample.pcap
```

## 项目结构

```
pcaptool/
├── src/
│   └── main.c        # 主程序
├── tools/
│   ├── make_sample.py  # 生成测试用 pcap 文件
│   └── make_doc.py     # 生成/更新学习笔记（输出到 docs/）
├── docs/
│   └── pcaptool学习笔记.docx    # 持续更新的逐步讲解文档
├── samples/          # 示例抓包文件
├── Makefile          # 编译脚本
└── README.md
```

## License

MIT

## 使用说明

```bash
# 读取并分析一个 pcap 文件
./pcaptool samples/sample.pcap

# 自行生成新的测试文件
python3 tools/make_sample.py

# 生成/更新学习笔记文档（需要 python-docx）
python3 tools/make_doc.py
```

## 第三方

- 本项目基于 [libpcap](https://www.tcpdump.org/) 抓包库。
