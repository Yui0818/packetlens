# PacketLens（网镜）

用 C 语言写的命令行网络抓包 / 分析工具，能读 pcap 文件、逐层拆协议头、做流量统计，也能实时抓网卡。

说白了就是照 tcpdump / Wireshark 的思路自己重写一遍，没打算替代它们，主要想弄明白一个数据包从网卡到屏幕上，中间到底被拆成了几层。

## 这是什么

`packetlens` 读取网络抓包文件（`.pcap` 格式），把里面的数据包逐个解析出来做统计。底层用的是 **libpcap**，也就是 Wireshark 和 tcpdump 用的同一个抓包库。

```
$ ./packetlens samples/sample.pcap
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

====== 协议统计 ======
TCP      3 个包   209 字节（47.9%）
UDP      1 个包   79 字节（18.1%）
ICMP     2 个包   148 字节（33.9%）

====== Top IP（收发都算）======
192.168.1.109    6 次
93.184.216.34    4 次
192.168.1.1    2 次

====== Top 端口（收发都算）======
54321     3 次
80     3 次
53     1 次
50000     1 次
```

## 功能

- [x] 读取 `.pcap` 文件
- [x] 遍历并打印每个包的长度 / 时间戳
- [x] 解析以太网 / IPv4 / TCP / UDP / ICMP 头
- [x] 按协议统计流量占比
- [x] 过滤表达式（如 `tcp port 80`）
- [x] Top IP / Top 端口 排名
- [x] 实时网卡抓包
- [x] 导出报告

## 为什么做这个

自学网络的时候看协议图总觉得懂了，真去写才发现每个字段的位置、字节序、校验和都得自己抠一遍才记得住。写这个项目就是为了逼自己把这层抠穿。

另外它练的东西挺全：位操作、内存布局、字节序、结构体对齐、链表排序，全是 C 的硬功夫。写完顺手还能当简历项目。

## 构建

依赖：Linux + GCC + libpcap 开发库。（Windows 上用 WSL 就行，我就是在 WSL2 里开发的。）

```bash
# Ubuntu / Debian
sudo apt install libpcap-dev

# 编译
make

# 运行
./packetlens samples/sample.pcap
```

## 项目结构

```
packetlens/
├── src/
│   └── main.c        # 主程序，整个工具就在这一个文件里
├── tools/
│   ├── make_sample.py  # 生成测试用 pcap 文件
│   ├── make_doc.py     # 生成/更新学习笔记（输出到 docs/）
│   ├── make_guide.py   # 生成《完全教程（小白版）》
│   ├── make_manual.py  # 生成《逐行手册》
│   ├── guide/          # 完全教程的各章节源码
│   └── manual/         # 逐行手册的各章节源码
├── docs/
│   ├── packetlens学习笔记.docx    # 开发历程 + 每版代码讲解
│   ├── packetlens完全教程.docx    # 小白版完全教程（9 章 + 4 附录）
│   └── packetlens逐行手册.docx    # 操作步骤手册 + 859 条逐行代码讲解
├── samples/          # 示例抓包文件
├── Makefile          # 编译脚本
├── push.bat          # 一键提交+推送（双击即用）
├── 更新文档.bat       # 一键更新三份文档（双击即用）
├── .gitattributes    # 让 GitHub 别把 tools/ 的 Python 算进语言统计
├── LICENSE           # MIT
└── README.md
```

那三份 Word 文档里的图和正文，也是项目里这几个 Python 脚本生成的，改完内容重跑一遍脚本就行。

## 使用说明

```bash
# 读取并分析一个 pcap 文件
./packetlens samples/sample.pcap

# 只看 TCP 80 端口的包（过滤：tcp / udp / icmp / port 80 / host 1.2.3.4，可组合）
./packetlens samples/sample.pcap tcp port 80

# 实时抓网卡（抓 20 个包自动停；Linux 下要 sudo，Ctrl+C 可提前停）
sudo ./packetlens live eth0

# 把分析结果导出成报告文件
./packetlens samples/sample.pcap --report 报告.txt

# 自行生成新的测试文件
python3 tools/make_sample.py

# 生成/更新学习笔记文档（需要 python-docx）
python3 tools/make_doc.py
```

## 一键脚本（Windows 双击即用）

- `push.bat`：提交当前改动并推到 GitHub
- `更新文档.bat`：重新生成三份 Word 并导出 PDF，收进桌面的「packetlens文档」文件夹

## 许可

MIT。

抓包用的是 [libpcap](https://www.tcpdump.org/)，协议字段和 pcap 文件格式的说明都来自 tcpdump.org 的公开文档；解析那部分代码是自己写的。
