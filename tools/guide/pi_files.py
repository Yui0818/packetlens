# -*- coding: utf-8 -*-
"""第 5 章：其余文件详解——Makefile、脚本、配置。"""

from docbuild import *

h1('第 5 章  其余文件详解')

para('main.c 是主角，但一个能拿得出手的项目还要有「配角团队」：让代码能编译的 Makefile、造测试数据的脚本、生成文档的脚本、一键脚本、配置和协议。这一章把它们逐个讲清楚。')

h2('5.1 Makefile 逐行：告诉 make 怎么编译')

para('在终端敲的 make 命令，其实什么都没干——它只是去读当前文件夹里的 Makefile（名字固定的配置文件），照着里面的指示干活。完整文件：')
code('CC = gcc\n'
     'CFLAGS = -Wall -Wextra -O2\n'
     'LIBS = -lpcap\n'
     '\n'
     'all: packetlens\n'
     '\n'
     'packetlens: src/main.c\n'
     '\t$(CC) $(CFLAGS) -o packetlens src/main.c $(LIBS)\n'
     '\n'
     'clean:\n'
     '\trm -f packetlens\n'
     '\n'
     '.PHONY: all clean')

bullet('CC = gcc：定义一个变量 CC，值是 gcc（GNU C 编译器）。用变量是为了「想换编译器时只改一处」。')
bullet('CFLAGS = -Wall -Wextra -O2：编译参数。Wall / Wextra 表示「把常见警告全打开」（我们追求零警告）；-O2 表示「二级优化」，让生成的可执行文件跑得更快。')
bullet('LIBS = -lpcap：要链接的库。字母 L 后面的 pcap 就是 libpcap——-l 的规则是「libpcap 写成 -lpcap」。')
bullet('all: packetlens：默认目标。敲 make 不带参数时执行 all，all 又指向 packetlens——意思是「产出 packetlens 这个文件」。')
bullet('packetlens: src/main.c 和下一行：核心编译规则。冒号前面是要生成的文件（packetlens），后面是「材料」（src/main.c）。下一行（以 Tab 开头）是具体命令：用 $(CC) $(CFLAGS) 把 main.c 编译成 -o packetlens（o = output），并链接 $(LIBS)。')
bullet('clean: 和 rm -f packetlens：打扫任务——make clean 会删掉编译产物。想「从零重新编译」时先 clean 一下最保险。')
bullet('.PHONY: all clean：声明 all 和 clean 是「动作名」而不是「文件名」——防止哪天你正好建了个叫 clean 的文件导致混乱。')
note('超级经典的一个坑：那些命令行的缩进必须是 Tab 键（制表符），不能用空格！这是 make 的历史规定。很多编辑器会自动把 Tab 转成空格，然后就报「missing separator」——如果你遇到这个错，先查缩进。')

h2('5.2 make_sample.py 逐行：用 Python 凭空造网络包')

para('测试需要数据。与其满世界找 pcap 文件，项目用 Python 脚本「凭空造」了一个——这也是一份绝佳的教材，因为它逼你把 pcap 的字节结构彻底想明白。')

h3('5.2.1 文件头：定义 pcap 的骨架')
code('MAGIC = 0xA1B2C3D4      # pcap 经典文件头的"魔数"（magic number）\n'
     'VERSION_MAJOR = 2\n'
     'VERSION_MINOR = 4\n'
     'GLOBAL_HEADER = struct.pack(\n'
     '    "<IHHiIII",\n'
     '    MAGIC, VERSION_MAJOR, VERSION_MINOR, 0, 0, 65535, 1,\n'
     ')')
bullet('魔法数字（magic number）：文件开头放一个特殊数 0xA1B2C3D4，像盖章一样宣告「我是 pcap 文件」。不同文件格式各有自己的魔数，程序读文件第一件事就是验章。')
bullet('struct.pack：Python 的「打包」工具——把数字按指定格式变成一串字节。引号里每个字母代表一个字段的类型：I = 4 字节无符号整数、H = 2 字节无符号整数、h = 2 字节有符号整数。')
bullet('"<" 开头表示小端（little-endian）：pcap 文件头格式规定用小端存。注意和网络包里的「大端」形成对比——文件格式（历史约定小端）和网络协议（规定大端）是两回事，这里两种都有，正好见证。')
bullet('后面那串值依次是：魔数、版本 2、版本 4、时区 0、时间精度 0、最大抓包长度 65535、链路层类型 1（1 = 以太网）。合起来就是 pcap 规定的 24 字节文件头。')

h3('5.2.2 五个「组装函数」：像叠积木一样叠出网络包')
para('网络包是层层套起来的，脚本里就写五个函数，一层一个：')
code('def eth_frame(payload, src_mac, dst_mac, ethertype):\n'
     '    return dst_mac + src_mac + struct.pack(">H", ethertype) + payload\n'
     '\n'
     'def ipv4(payload, src, dst, proto, ident):\n'
     '    ...（20 字节 IP 头 + payload）\n'
     '\n'
     'def tcp(payload, sport, dport, seq, flags):\n'
     '    ...（20 字节 TCP 头 + payload）\n'
     '\n'
     'def udp(payload, sport, dport):\n'
     '    ...（8 字节 UDP 头 + payload）\n'
     '\n'
     'def icmp(payload, icmp_type, code, ident, seq):\n'
     '    ...（8 字节 ICMP 头 + payload）')
bullet('注意 eth_frame 那句开头的 +：Python 里字符串/字节串用 + 就能拼接。dst_mac + src_mac + 类型 + 内容——直接照抄以太网头的真实顺序，代码本身就在讲协议。')
bullet('">H" 和前面的 "<" 相反：> 表示大端。ethertype、端口、长度这些网络字段全部用大端打包——因为网络协议规定大端。同一个脚本里，文件头用小端、包字段用大端，两种都出现了，正好是活教材。')
bullet('每个函数都是「造这一层头 + 接上上层内容」——这正是一条真实的包被「封装」的过程，只是方向反过来（我们是自上而下组装）。')

h3('5.2.3 主程序：组装六个包')
code('    syn = eth_frame(\n'
     '        ipv4(tcp(b"", sport=54321, dport=80, seq=100, flags=0x02),\n'
     '             src=ip_a, dst=ip_web, proto=6, ident=1),\n'
     '        mac_a, mac_b, 0x0800)')
bullet('看这个嵌套：最里层 tcp(...) 造 TCP 头（flags=0x02 就是 SYN）；把它当 payload 套进 ipv4(...)；再套进 eth_frame(...)——三层嵌套写完，一个完整的 SYN 包诞生。之后 packets.append 收进列表。')
bullet('六个包依次是：TCP SYN、TCP SYN+ACK、UDP DNS 查询、TCP 数据包（PSH+ACK）、ICMP ping 请求、ICMP ping 应答——正好覆盖工具要解析的全部情况。flags=0x02 / 0x12 / 0x18 对应 SYN / SYN+ACK / PSH+ACK（第 2.6 节讲的三个标志组合）。')
bullet('开头那些 b"..." 是 Python 的「字节串」字样——TCP 数据包里塞的假 HTTP 请求正文就是用它写的。')

h3('5.2.4 写文件')
code('def write_pcap(path, packets):\n'
     '    out = bytearray(GLOBAL_HEADER)\n'
     '    for ts_sec, ts_usec, data in packets:\n'
     '        out += struct.pack("<IIII", ts_sec, ts_usec, len(data), len(data))\n'
     '        out += data\n'
     '    with open(path, "wb") as f:\n'
     '        f.write(out)')
bullet('bytearray：一个「可以不断追加的字节串」（bytes 是不可变的，bytearray 可以 +=）。')
bullet('for 循环：每个包先写 16 字节小包头（时间戳秒、微秒、实际长度、保存长度——两个长度这里一样），再写包本体。全是小端 "<"。')
bullet('with open(path, "wb")：以「二进制写」模式打开文件并写入全部字节。with 是 Python 的特殊语法：代码块结束时自动关文件，不用手动 fclose（对比第 4.18 节 C 里的手写 fclose——两种语言的性格差异一目了然）。')

h2('5.3 make_doc.py 和 guide/：项目自己给自己写文档')

para('你手里的《学习笔记》就是 tools/make_doc.py 生成的；你正在读的这本《完全教程》则是 tools/guide/ 文件夹里十来个章节脚本 + tools/make_guide.py 拼出来的。原理和 main.c 里写报告一章一样：内容以代码（python-docx 的排版指令）的形式存放，需要时一键重新生成。')
bullet('资料和代码同仓库、同提交——代码到哪一版，文档讲到哪一版，永远不会「文档过时」。')
bullet('对学习者来说还有个好处：想改文档、加章节，只要找到对应段落改文字、重新运行脚本即可，不用手工和 Word 排版搏斗。')

h2('5.4 push.bat 逐行：双击一下，代码传上云端')

para('这是个 Windows 批处理文件（.bat），双击就能运行——它的使命是把当前所有改动提交并推送到 GitHub：')
code('@echo off\n'
     'cd /d "%~dp0"\n'
     '\n'
     'git add -A\n'
     'git status --short\n'
     '\n'
     'set CHANGED=\n'
     'for /f "delims=" %%i in (\'git status --short\') do set CHANGED=1\n'
     'if not defined CHANGED (\n'
     '    echo "没有待提交的改动，备份结束（代码已在 GitHub 上）。"\n'
     '    goto :push\n'
     ')\n'
     '\n'
     'set /p MSG="请输入本次提交说明（直接回车用默认）: "\n'
     'if "%MSG%"=="" ( set MSG=update %date% %time% )\n'
     '\n'
     'git -c user.name="Yui0818" -c user.email="324952380+Yui0818@users.noreply.github.com" commit -m "%MSG%"\n'
     'if errorlevel 1 ( echo 提交失败，请检查。 & pause & exit /b 1 )\n'
     '\n'
     ':push\n'
     'git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin master\n'
     '...（提示成功/失败，pause 停住窗口）')
bullet('@echo off：批处理的「开场白」，表示「不要把我执行的每条命令都打印出来」——不然窗口里全是噪音。')
bullet('cd /d "%~dp0"：把工作目录切到「这个 bat 文件所在的文件夹」。%~dp0 是批处理的魔法变量（d = 盘符、p = 路径），这样不管你从哪双击它，都在项目文件夹里干活。')
bullet('git add -A：把所有改动放进「暂存区」（准备提交清单）。git status --short 再把清单显示出来给你看。')
bullet('那个 for 循环：执行 git status，如果有任何输出（有文件进来），就设一个标记 CHANGED=1。')
bullet('if not defined CHANGED：如果一个改动都没有，提示「无需备份」并跳去 push 步骤。')
bullet('set /p MSG=...：停下来等你输入一句提交说明。直接回车的话，MSG 是空的，下一行就给它填一个默认值（update + 日期时间）。')
bullet('git -c user.name=... commit：提交。-c 是「临时设置」——只在这一次命令里把提交者名字设成 Yui0818、邮箱设成 GitHub 提供的隐私邮箱（noreply）。这样 GitHub 才会把提交算在你的账号名下（contributors 里只有你）。用户名邮箱里没有任何 AI 署名——这个项目所有的提交记录都干干净净属于你。')
bullet('if errorlevel 1：上一条命令失败（返回码 ≥ 1）就提示失败并停住。')
bullet('最后一行推送：-c http.proxy=... 临时给 git 设代理（127.0.0.1:7897 是本机的网络代理端口）——保证在国内网络环境下也能顺利推送到 GitHub。')

h2('5.5 更新文档.bat 逐行：一键刷新两份 Word')

code('@echo off\n'
     'cd /d "%~dp0"\n'
     'wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/Projects/packetlens && python3 tools/make_doc.py"\n'
     'copy /y "docs\\packetlens学习笔记.docx" "%USERPROFILE%\\Desktop\\packetlens学习笔记.docx" >nul\n'
     'echo 已更新：docs\\packetlens学习笔记.docx（并复制到桌面）\n'
     'pause')
bullet('中间那行：调用 WSL，进入项目目录，运行生成《学习笔记》的 Python 脚本。wsl.exe 是 Windows 直接调用 Linux 的入口。')
bullet('copy /y：把仓库里的文档复制一份到桌面（%USERPROFILE% 是「当前用户的主目录」，/y 表示「覆盖时不再问」）。这样你随时在桌面上就能打开最新版。')
bullet('pause：运行完停一下，让你能看到结果再关窗口——不然双击的窗口「闪一下就没了」。')

h2('5.6 .gitignore：告诉 git「这些别管」')

code('# 编译出来的可执行程序，不应该上传（别人自己 make 就行）\n'
     'packetlens\n'
     '\n'
     '# 编译过程中的临时/目标文件\n'
     '*.o\n'
     '*.obj\n'
     '\n'
     '# 各种 IDE 或系统生成的杂文件\n'
     '.vscode/\n'
     '.idea/\n'
     '*.swp\n'
     'Thumbs.db\n'
     '.DS_Store')
bullet('规则：一行一条。不带斜杠 = 匹配文件或文件夹；带 / 结尾 = 只匹配文件夹；* 是通配符（任意字符）。')
bullet('为什么不传可执行文件？①它是编译的产物，代码改一行就能重新生成，没必要存；②不同系统的可执行文件不同（Windows 的 exe 在 Mac 上没用）；③省仓库空间。好的开源仓库都只存「源代码 + 资源」，不存「编译结果」。')

h2('5.7 LICENSE：MIT 协议的通俗解释')

para('仓库里的 LICENSE 文件写着 MIT 协议——地球上最宽松、最常见的开源协议之一。用大白话翻译：')
bullet('任何人都可以自由使用、修改、分发你的代码，甚至拿去商用——不用付钱、不用打招呼')
bullet('唯一的条件：他们分发时要保留你的版权声明（那段 "Copyright (c) 2026 刘梓涵"）')
bullet('你不对代码的使用后果负责（免责条款）——别人拿去用出了问题不能怪你')
para('给项目加协议的意义：告诉世界「这代码开放使用」。「没有协议」的公开代码在法律上是「保留所有权利」的，别人反而不敢用。开源项目标配：代码 + README + LICENSE 三件套。')

h2('5.8 README.md：项目的门面')

para('GitHub 上每个仓库的首页显示的就是 README.md 的内容——它是别人（面试官！）点进来第一眼看到的东西。本项目 README 的结构可以当模板：')
bullet('项目名 + 一句话定位：让人 3 秒知道「这是什么」')
bullet('运行示例：一段真实输出，比一千句形容词都有说服力')
bullet('功能清单：带勾选框（- [x]），已完成 / 待办的进度一目了然')
bullet('为什么做这个：展示动机，也是讲给面试官听的')
bullet('构建方法：怎么从源码到能跑的步骤（复制粘贴即用）')
bullet('项目结构 + 使用说明 + 一键脚本：让人快速上手')
bullet('License 和第三方说明：规范与致谢')
note('写 README 的黄金法则：假设读者是个着急的人——他扫一眼就要知道这个项目是干嘛的、值不值得细看。所以「一句话定位 + 一段真实输出」永远放在最上面。')

para('到这里，项目里的每个文件都过了一遍。下一章是纯实操：把工具真正用起来，顺便配一份「报错急救箱」。')
