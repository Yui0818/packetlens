# -*- coding: utf-8 -*-
"""第 6 章：使用手册 + 报错急救箱。"""

from docbuild import *

h1('第 6 章  使用手册 + 报错急救箱')

para('这一章是纯实操：假设你现在坐到电脑前，从零开始把每个功能用一遍。每一步都配「应该看到什么」，对不上就去 6.8 的急救箱。')

h2('6.1 第一步：打开 WSL、进入项目')

para('打开方式：开始菜单搜索「Ubuntu」或「WSL」，打开那个黑色/紫色的终端窗口。然后输入：')
code('cd /mnt/d/Projects/packetlens')
para('cd 是 change directory 的缩写，就是切换文件夹。这句的意思是：进到 D 盘里 Projects 下的 packetlens（在 WSL 里，D 盘写作 /mnt/d）。')
para('怎么确认进对了？敲这两个命令看看：')
code('$ pwd\n'
     '/mnt/d/Projects/packetlens\n'
     '$ ls\n'
     'LICENSE  Makefile  README.md  docs  packetlens  push.bat  samples  src  tools  更新文档.bat')
bullet('pwd 打印「我现在在哪」，应该输出 /mnt/d/Projects/packetlens。')
bullet('ls 列出「这里有什么」。把上面那串文件名都看到就对了，packetlens 是编译产物，第一次可能还没有，没关系，下一步就生成。')

h2('6.2 第二步：编译（make）')

code('$ make')
para('预期输出只有一行 gcc 命令，可能还带一行 rm。编译成功会在原地生成一个叫 packetlens 的可执行文件。')
bullet('什么时候要重新 make？只要你改了 src/main.c，哪怕只改一个字母，都得重新 make 才生效。程序是编译出来的，不是直接读代码。')
bullet('想「从零重来」：先 make clean（删掉编译产物）再 make，最干净。')
bullet('编译要几秒？本项目很小，通常一两秒内完成。')

h2('6.3 第三步：分析一个 pcap 文件')

code('$ ./packetlens samples/sample.pcap')
para('然后屏幕上会滚出六个包的完整拆解 + 统计报告。对照第 3 章 3.4 的输出看，应该一模一样。')
para('读输出分三个层次：')
bullet('想快速扫，每行看「协议名字」就够了，先弄清这段流量由什么组成，里面有 TCP、UDP 和 ping。')
bullet('细看某个包的话，从「以太网」那行一路读到「TCP/UDP/ICMP」行，有点像在读一棵树。')
bullet('懒得全看就直接翻到最后的统计：协议占比、Top IP、Top 端口，30 秒摸清整段流量。')

h2('6.4 过滤：只看你想看的包')

para('用法：把过滤条件写在文件名后面。支持的关键词和组合：')
code('$ ./packetlens samples/sample.pcap tcp          # 只有 TCP 包\n'
     '$ ./packetlens samples/sample.pcap udp          # 只有 UDP 包\n'
     '$ ./packetlens samples/sample.pcap icmp         # 只有 ping 包\n'
     '$ ./packetlens samples/sample.pcap port 80      # 收发端口里有 80 的包\n'
     '$ ./packetlens samples/sample.pcap tcp port 80  # TCP 且沾 80 端口\n'
     '$ ./packetlens samples/sample.pcap host 192.168.1.1   # 和这个 IP 来往的包')
para('观察「跳号」：过滤 tcp port 80 时输出是 #1 #2 #4，中间少掉的那个编号就是被过滤的包。最后那句「已过滤掉 X 个包」会如实汇报。')
bullet('组合规则：多个条件写在一起就是「并且」，tcp port 80 就是协议是 TCP 而且端口有 80。')
bullet('写错了会怎样？比如把 port 写成「pot」，程序会打印支持的写法示例后退出。它不猜你的意思，这也是一种保护。')

h2('6.5 导出报告：把结果存成文件')

code('$ ./packetlens samples/sample.pcap --report 报告.txt')
para('运行结束后，除了屏幕上的输出，还会多一句「报告已写入: 报告.txt」，当前文件夹里就多出了这个文件，或者你指定的那个路径。打开看看：总览 + 协议统计 + Top IP + Top 端口。')
bullet('报告可以和过滤合用：./packetlens samples/sample.pcap tcp --report tcp报告.txt，这样报告里只统计 TCP 那部分。')
bullet('文件名自己定；写绝对路径（如 /tmp/my.txt）也行。')

h2('6.6 实时抓包：看活的流量')

code('$ sudo ./packetlens live lo 3')
bullet('sudo：以管理员身份运行。实时抓包要打开网卡的「混杂模式」，也就是顺便听别人的包，这个权限只有 root 有，不加 sudo 会报「permission denied」。')
bullet('live 后面的第一个参数是网卡名字：lo 是「本机内部通信」的虚拟网卡；eth0 是以太网口；不写默认 any，所有网卡合在一起听。')
bullet('第二个参数是要抓几个包，不写默认 20 个。抓满自动停，想提前停就按 Ctrl+C。')
bullet('WSL 小贴士：在 WSL 里想看到「有内容」的输出，最好同时制造点网络活动，比如另开个终端 ping 一下外网，或者浏览器刷个网页。安安静静的时候它会显示「正在监听……」，那是正常的，它在等包。')
note('真实踩坑记录：如果抓包过程中用别的方式强杀程序（比如 timeout 命令），你可能一点输出都看不到，因为程序的打印内容还在缓冲区里，没来得及写出来就被杀了。正常结束（抓满、或者 Ctrl+C）就不会有这个问题。C 程序「输出缓冲」的经典现象，遇到别慌。')

h2('6.7 辅助命令备忘卡（建议截图保存）')

code('make                                  # 编译\n'
     'make clean                            # 删掉编译产物\n'
     './packetlens samples/sample.pcap        # 完整分析\n'
     './packetlens samples/sample.pcap tcp port 80      # 过滤分析\n'
     './packetlens samples/sample.pcap --report r.txt   # 导出报告\n'
     'sudo ./packetlens live lo 5             # 实时抓 5 个包\n'
     'python3 tools/make_sample.py          # 重新生成测试数据\n'
     'python3 tools/make_doc.py             # 重新生成《学习笔记》\n'
     'python3 tools/make_guide.py           # 重新生成《完全教程》\n'
     'git status                            # 看看有什么改动还没提交\n'
     'git log --oneline                     # 看提交历史')
para('Windows 侧不用进 WSL：双击项目里的 push.bat 就是提交并推送；双击 更新文档.bat 会刷新两份 Word 并复制到桌面。')

h2('6.8 报错急救箱（按错误信息查）')

qa('make: command not found / gcc: command not found',
   '编译工具没装。在 WSL 里运行 sudo apt update && sudo apt install build-essential 安装编译套件。你这台电脑已经装好了，这段是留给重装系统的备忘。')
qa('fatal error: pcap/pcap.h: No such file or directory',
   'libpcap 的开发包没装。运行 sudo apt install libpcap-dev 即可。这正是编译命令里 -lpcap 要链接的那个库。')
qa('Makefile:3: *** missing separator. Stop.',
   'Makefile 里命令行前面的缩进被换成了空格，必须用 Tab 键。用编辑器把那一行重新用 Tab 缩进。这是 make 最著名的坑，没有之一。')
qa('./packetlens: No such file or directory（但你明明看到了这个文件）',
   '两种可能：①忘了先 make；②忘了写 ./。直接敲 packetlens，系统会去「系统目录」里找，找不到就报这个错。')
qa('bash: cd: /mnt/d/projects/packetlens: No such file or directory',
   '路径拼写或大小写问题。Linux 区分大小写：Projects 不等于 projects。用 ls 一层层确认。')
qa('sudo: ./packetlens: command not found',
   'sudo 运行时的工作目录问题，或者路径写法（sudo 里也要写 ./packetlens 或完整路径）。先确认 make 过、且在正确目录。')
qa('打不开网卡 lo : ... Permission denied',
   '实时抓包忘了加 sudo。普通用户没有打开混杂模式的权限。')
qa('live 模式一直在「正在监听」，屏幕不动',
   '没等到包。可能这个网卡上真的暂时没流量，试试指定 lo 并同时制造流量（另开终端 ping 网关），或者干脆用 any。按 Ctrl+C 随时能退。')
qa('报告文件打不开: xxx',
   '路径写错了（比如往一个不存在的文件夹写），或者没有权限。换成当前目录下的简单文件名试试。')
qa('push.bat 双击后提示推送失败',
   '多半是代理没开。push 走的是本机 127.0.0.1:7897 端口的代理，先把代理软件（SakuraCat）打开再试。也可能就是网络抖了一下，重试一次。')
qa('在 WSL 里编辑代码，用哪个编辑器？',
   '本项目推荐 VS Code：在项目目录里敲 code . 就会打开（WSL 集成）。当然用 vim/nano 也完全可以。')
qa('改了代码发现改坏了，怎么反悔？',
   '如果还没提交：git checkout -- 文件名 可以丢弃这个文件的未提交改动（慎用，丢的就是丢的）。如果已经提交过：git log 找到上一个好版本，git revert 或 git reset 回退。第 7 章讲了怎么在 GitHub 网页上看历史来帮你判断。')

h2('6.9 三个成长任务（动手才算学会）')

para('照着做，卡住了就回这章查：')
bullet('任务一：用 python3 tools/make_sample.py 重新生成测试数据，然后再跑一遍 ./packetlens samples/sample.pcap，体会一下「数据是人造的，但格式完全真实」。')
bullet('任务二：给输出加点东西。打开 src/main.c，找到 print_packet 里打印 ICMP 那段，在「回显请求」后面补一句你自己的话，重新 make 再跑。第一次亲手改 C 代码并看到效果。')
bullet('任务三：改完先 git status 看看改动，再双击 push.bat 提交推送。去 GitHub 上找到你这笔提交，点开看 diff（绿色是你加的）。恭喜，你已经走完了一整个专业开发者的日常循环。')

para('下一章把 GitHub 网页的每个角落都讲透，那是大家天天看到、却一直没看懂的地方。')
