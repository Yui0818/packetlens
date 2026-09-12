#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_sample.py —— 生成一个标准的 pcap 测试文件
================================================
这个脚本不依赖任何外网资源，纯手工用 Python 构造一批"真实格式"的网络包，
写到 samples/sample.pcap 里，给 pcaptool 测试用。

pcap 文件格式（全局头 + 若干数据包）：
  - 全局头（24 字节）：说明"这是 pcap 文件、时间精度、链路层类型"
  - 每个数据包（16 字节包头 + 原始数据）：
      ts_sec(4) ts_usec(4) caplen(4) len(4) + 包体

我们用 Python 的 struct 模块按字节写出文件。这样你能看到"网络包
在磁盘上到底长什么样"。
"""

import struct

MAGIC = 0xA1B2C3D4      # pcap 经典文件头的"魔数"，读到它就知道是 pcap
VERSION_MAJOR = 2
VERSION_MINOR = 4
# thiszone(4) sigfigs(4) snaplen(4) network(4)
GLOBAL_HEADER = struct.pack(
    "<IHHiIII",
    MAGIC, VERSION_MAJOR, VERSION_MINOR, 0, 0, 65535, 1,  # network=1 表示"以太网"
)


def eth_frame(payload: bytes, src_mac: bytes, dst_mac: bytes, ethertype: int):
    """把一段数据包上'以太网头'。返回 14 字节的以太网帧头 + payload。
    ethertype 0x0800 = IPv4, 0x0806 = ARP。"""
    return dst_mac + src_mac + struct.pack(">H", ethertype) + payload


def ipv4(payload: bytes, src: bytes, dst: bytes, proto: int, ident: int):
    """构造一个 IPv4 头 + payload。proto: 6=TCP, 17=UDP, 1=ICMP."""
    # 版本4+首部长度5(20字节) + DS + 总长 + ident + flags/frag + ttl + proto + 校验和 + src + dst
    ihl = 0x45                     # 0100 0101: 版本4, 首部5*4=20字节
    tos = 0
    total_len = 20 + len(payload)
    flags_frag = 0                 # 无分片
    ttl = 64
    # 校验和这里填 0 即可，Wireshark/pcap 工具能看懂
    checksum = 0
    header = struct.pack(
        ">BBHHHBBH4s4s",
        ihl, tos, total_len, ident, flags_frag, ttl, proto, checksum, src, dst,
    )
    return header + payload


def tcp(payload: bytes, sport: int, dport: int, seq: int):
    """构造一个 TCP 头 + payload。20 字节标准 TCP 头。"""
    data_offset = 5 << 4           # 首部 5 个字 = 20 字节
    flags = 0x18                   # 0x18 = PSH+ACK (常用)
    window = 65535
    checksum = 0
    urg = 0
    header = struct.pack(
        ">HHIIBBHHH",
        sport, dport, seq, 0, data_offset, flags, window, checksum, urg,
    )
    return header + payload


def udp(payload: bytes, sport: int, dport: int):
    """构造一个 UDP 头 + payload。8 字节 UDP 头。"""
    length = 8 + len(payload)
    checksum = 0
    header = struct.pack(">HHHH", sport, dport, length, checksum)
    return header + payload


def write_pcap(path, packets):
    """packets: 一个列表，每项是 (时间戳秒, 微秒, 原始字节)。
    按 pcap 格式写出整个文件。"""
    out = bytearray(GLOBAL_HEADER)
    for ts_sec, ts_usec, data in packets:
        out += struct.pack("<IIII", ts_sec, ts_usec, len(data), len(data))
        out += data
    with open(path, "wb") as f:
        f.write(out)
    print(f"已生成 {path}  共 {len(packets)} 个包  总大小 {len(out)} 字节")


def main():
    # 一些方便的字节：MAC 地址 6 字节，IP 地址 4 字节
    mac_a = bytes.fromhex("001122334455")     # 来源设备 MAC
    mac_b = bytes.fromhex("aabbccddeeff")     # 目标 MAC
    ip_a = bytes([192, 168, 1, 109])          # 来源 IP
    ip_b = bytes([192, 168, 1, 1])            # 网关/服务器 IP
    ip_web = bytes([93, 184, 216, 34])        # 一个外网 IP (example.com)

    packets = []
    ts = 1700000000   # 随便一个时间戳

    # --- 包1: TCP 三次握手的第一步 SYN (来包) ---
    syn = eth_frame(
        ipv4(tcp(b"", sport=54321, dport=80, seq=100),
             src=ip_a, dst=ip_web, proto=6, ident=1),
        mac_a, mac_b, 0x0800)
    packets.append((ts, 100, syn))

    # --- 包2: 服务器回 SYN-ACK ---
    synack = eth_frame(
        ipv4(tcp(b"", sport=80, dport=54321, seq=1000),
             src=ip_web, dst=ip_a, proto=6, ident=2),
        mac_b, mac_a, 0x0800)
    packets.append((ts, 200, synack))

    # --- 包3: 一个 UDP DNS 查询 (查询 getexample.com 的域名) ---
    dns_payload = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"  # 简化的 HTTP 请求内容
    udp_pkt = eth_frame(
        ipv4(udp(dns_payload, sport=53, dport=50000),
             src=ip_web, dst=ip_a, proto=17, ident=3),
        mac_b, mac_a, 0x0800)
    packets.append((ts, 300, udp_pkt))

    # --- 包4: 再一个 TCP 数据包 (横幅携带内容) ---
    payload = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"
    data_pkt = eth_frame(
        ipv4(tcp(payload, sport=54321, dport=80, seq=200),
             src=ip_a, dst=ip_web, proto=6, ident=4),
        mac_a, mac_b, 0x0800)
    packets.append((ts, 400, data_pkt))

    write_pcap("samples/sample.pcap", packets)


if __name__ == "__main__":
    main()
