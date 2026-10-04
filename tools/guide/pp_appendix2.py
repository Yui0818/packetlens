# -*- coding: utf-8 -*-
"""附录 E：动手练习 25 题；附录 F：面试 25 问。"""

from docbuild import *

# ============================================================
# 附录 E
# ============================================================
h1('附录 E  动手练习 25 题（附答案要点）')

para('练习怎么用：先自己答，再看答案要点。所有题目只靠这个项目里的东西就能做出来，不用去翻别的资料。分组从易到难：热身、读代码、动手改。')

h2('E.1 热身题（1~8：看和玩）')

para('第 1 题：不查文档，写出「在 WSL 里进入项目并跑完整分析」的最短命令序列（两条命令）。')
note('答案要点：先 cd /mnt/d/Projects/packetlens，再跑 ./packetlens samples/sample.pcap。要是还没编译过，中间得插一句 make。')

para('第 2 题：跑一遍完整分析，数一数：六个包里几个 TCP、几个 UDP、几个 ICMP？')
note('答案要点：TCP 3 个（包 1、2、4），UDP 1 个（包 3），ICMP 2 个（包 5、6）。')

para('第 3 题：只用过滤功能把「ping 的两个包」单独显示出来，命令怎么写？输出里的编号是哪几个？')
note('答案要点：./packetlens samples/sample.pcap icmp；编号是 #5 和 #6，它们是连着的两个，中间没有跳号。')

para('第 4 题：把过滤切换成 host 192.168.1.1，为什么结果和上一题一样？再用 host 93.184.216.34 试试，结果为什么不同？')
note('答案要点：样例里只有 ping 那两个包沾 192.168.1.1；93.184.216.34 是网站 IP，沾它的是包 1、2、3、4，一共四个。')

para('第 5 题：导出一份报告到「我的报告.txt」，然后回答：报告里有没有「已过滤掉」这一行？为什么？')
note('答案要点：没有。因为没加过滤条件，filtered 是 0，那一行只在真过滤过的时候才打印。可以加上 icmp 再导出一次，对比看看。')

para('第 6 题：不看屏幕，猜一猜：统计里 Top 端口为什么 54321 和 80 都是 3 次？')
note('答案要点：握手一来一回再加数据包。54321 出现 3 次（源、目的、源），80 也是 3 次（目的、源、目的），规则是收发都算。')

para('第 7 题：实时抓包时不写网卡名，程序默认用什么？抓 10 个包怎么写？')
note('答案要点：默认 "any"；抓 10 个可以写 sudo ./packetlens live any 10，只写 sudo ./packetlens live 10 也一样。')

para('第 8 题：故意写一个错的过滤词（比如 port abc），程序会怎样？为什么说这个设计是「好的」？')
note('答案要点：打印支持的写法示例后退出，返回码是 1。这么设计的好处是宁可明确报错，也不去猜用户的意思，猜错的代价更大。')

h2('E.2 读代码题（9~17：看代码回答问题）')

para('第 9 题：rd16 为什么先 <<8 再相或？用 0x12、0x34 两个字节手动演算一遍。')
note('答案要点：0x12 是高位（网络大端约定），<<8 变成 0x1200；再 | 0x34 得到 0x1234。')

para('第 10 题：parse_packet 在什么情况下返回 0？什么情况下返回 1 但带 note？各举一例。')
note('答案要点：返回 0 表示连 14 字节的以太网头都不完整；返回 1 带 note 的例子有「IPv4 头部不完整」「这是分片的后续片…」「TCP 头部不完整」这些，属于部分成功。')

para('第 11 题：print_packet 里第一个「提前 return」在哪一行？它拦住了什么情况？')
note('答案要点：第 247 行，也就是 ethertype 不是 IPv4 那个分支里的 return。它拦住 ARP、IPv6 这些非 IPv4 的包，打印一句说明就不往下走了。')

para('第 12 题：counter_add 里，为什么「找到了就立刻 return」？如果忘了这个 return 会发生什么？')
note('答案要点：立刻返回是为了不再执行「插入新行」的逻辑；忘了 return 的话，同一个 key 会被重复插入新行（次数还停在 1），统计就错了。')

para('第 13 题：stats_update 的第一行 if 是干嘛的？如果去掉它，把一个 ARP 包喂进来会怎样？')
note('答案要点：把「非 IPv4」的包过滤掉。去掉之后 ARP 包的 has_ipv4 = 0，后面 proto 这些字段就是无意义的默认 0，程序不会崩，但统计会被污染，比如把它当成未知协议。')

para('第 14 题：filter_match 里端口条件的两个「不等于」中，用的是 && 还是 ||？为什么必须是这个？')
note('答案要点：用的是 &&，源端口不等于 AND 目的端口不等于才拒绝，意思是「任何一头沾上就算通过」。写成 || 就变成「源或目的任意一头不匹配就拒绝」，等于逼着两头都相等，语义完全反了。')

para('第 15 题：handle_packet 里 shown_bytes 和 bytes 有什么区别？统计百分比时用的哪个？')
note('答案要点：bytes 是读进来的所有包的总长，shown_bytes 是「显示出来」的包的总长。emit_stats 收到的参数是 shown_bytes，所以统计只算显示的那部分。')

para('第 16 题：main 里那个「atoi(argv[3]) > 0」判断，如果用户写的是 live eth0 tcp，会走哪个分支？为什么？')
note('答案要点：不走数量分支。atoi("tcp") 返回 0，不满足 >0，于是 filter_start 保持 3，"tcp" 被当成过滤词解析。本来就该这样。')

para('第 17 题：write_report 里为什么必须先检查 f == NULL？不检查会在哪一行出问题？')
note('答案要点：fopen 失败时会返回 NULL，比如路径不存在或者没权限。不检查的话，下一行 fprintf(f, ...) 就在对空指针操作，程序多半会崩。')

h2('E.3 动手改代码题（18~25：改完要能重新 make 并看到效果）')

para('第 18 题：把默认抓包数量从 20 改成 30。（提示：找 live_count。）')
note('答案要点：main 里 int live_count = 20; 改成 30，重新 make。然后 ./packetlens live lo 试试默认值，记得加 sudo。')

para('第 19 题：让 UDP 那行输出多打印一句「（无连接协议）」。')
note('答案要点：在 print_packet 的 UDP 分支的 printf 后面加一句 printf("    （无连接协议）\\n");。')

para('第 20 题：给 ICMP 输出加上「序号」字段的显示。提示：序号在 ICMP 头的第 5、6 字节，动手分三步，PacketInfo 里加字段、parse_packet 里读出来、print_packet 里打印。')
note('答案要点：三处动刀，结构体加 icmp_seq；parse 里 icmp_seq = rd16(transport + 6);；打印里加 %u。走完这一遍「加字段」的完整循环，这种改动往后会经常遇到。')

para('第 21 题：把 Top 榜的显示数量从 5 改成 3。（提示：两处 limit。）')
note('答案要点：emit_stats 里两个 int limit = ... : 5; 都改成 3。')

para('第 22 题：让程序支持一个「只看前 N 个包」的功能，比如 ./packetlens file.pcap first 5。说说你的改法思路，不要求全写对。')
note('答案要点：参数解析里先认领 first 和它后面的数字，存成全局 limit_show；handle_packet 显示前判断一下 shown < limit_show，超了就跳过显示，也可以直接 break 掉整个循环。这题练的就是从需求找改动点。')

para('第 23 题：给报告文件开头加一行「生成时间」。提示：C 里拿当前时间要引入 <time.h> 用 time()/localtime()。做不出来就只写出「需要在哪一步加」。')
note('答案要点：在 write_report 里 fprintf 标题行之后，用 time_t t = time(NULL); struct tm *lt = localtime(&t); fprintf(f, "生成时间: %04d-%02d-%02d %02d:%02d\\n", ...)。顺带走一遍「引入新工具箱 → 查它怎么用」的流程。')

para('第 24 题：故意把 parse_packet 里 if (len < 14) 改成 if (len < 10)，编译运行看看会不会出问题。为什么样例数据看不出问题？')
note('答案要点：样例都是完整包，不会触发；但理论上会把 10~13 字节的畸形包放进来，读到越界的 mac/ethertype。防御性检查平时看着没用，出事的时候才知道它值钱。改完记得改回去。')

para('第 25 题（综合）：给项目加一个新协议的支持，也就是 ARP。要求：识别 ARP 包，打印出「谁是 IP 的发包者、在找哪个 IP」。提示：ARP 头在以太网头之后，前 2 字节硬件类型、2 字节协议类型、1+1 字节长度、2 字节操作码、然后 6+4+6+4 字节的地址。先只做「打印一句 ARP 请求/应答」也算完成。')
note('答案要点：这题算「期末考试」那种，涉及以太网类型判断（0x0806 分支已经有了）、新的解析代码、PacketInfo 加字段、打印。哪怕先只做到「识别并打印操作码 1=请求/2=应答」，也已经完整走过一遍「给工具加协议」的流程。')

# ============================================================
# 附录 F
# ============================================================
h1('附录 F  面试 25 问（附答题要点）')

para('这些是 C 基础、网络基础、项目相关、git 四个方向的常见面试题。答案都尽量短，面试要的是你把话说清楚，不是背课文。')

h2('F.1 C 语言（8 问）')
qa('const 是什么意思？', '「只读」承诺，编译器帮你盯着这个变量/指针别被改。本项目里所有解析函数的指针参数都带 const，意思是「只读，不改别人的数据」。')
qa('static 用在函数上是什么意思？', '「本文件私有」，别的文件看不见，链接时也不会撞名字。本项目就一个文件，暂时用不上，不过以后要拆文件就省事了。')
qa('指针和数组什么关系？', '数组名在大多数场景下会「退化」成指向首元素的指针；但数组有长度信息，sizeof 能拿到，指针没有——所以我们每个函数都要额外传一个 len。')
qa('C 语言函数参数是怎么传递的？', '全部按值传递。想让函数改我的变量，就得传它的地址，也就是指针，本项目的 PacketInfo *info、FILE *f 都是这个用法。')
qa('位运算都用在哪了？举个例子。', '三个典型：二进制拼字节（rd16 的 << 和 |）、取字段（ihl 的 & 0x0F）、查标志位（TCP 标志的 f & 0x02）。')
qa('malloc 和 free 是干嘛的？这个项目为什么没用？', '动态申请/释放堆内存。本项目的数据都放在栈上或者静态区，大小一开始就知道，用不着动态内存，也就压根没有内存泄漏这回事。第 10.14 节讲过完整的理由。')
qa('结构体可以直接互相赋值吗？数组呢？', '结构体可以整体赋值（counter_sort 里的交换就用到了）；数组不行，必须逐元素搬（parse_packet 搬 MAC 用的循环）。')
qa('编译警告重要吗？', '重要。本项目一直保持「零警告」，我们真修过一个「可能未初始化」的警告，用 {0} 清零解决的。这类警告经常是真 bug 的前兆。')

h2('F.2 网络（8 问）')
qa('TCP 三次握手的过程？', 'SYN → SYN+ACK → ACK。目的是让双方都确认：我能发、你能收，你也能发给我。项目里的包 1、2 就是前两步。')
qa('TCP 和 UDP 的区别？', 'TCP：有连接、可靠、有序、有重传（像打电话）；UDP：无连接、不保证到达（像寄明信片），换来简单快速。')
qa('为什么 DNS 查询用 UDP？', '单次请求响应小、要求快，没有「建立连接」的价值；丢了就再问一次（应用层兜底），比 TCP 握手便宜。')
qa('MAC 地址和 IP 地址有什么区别？', 'MAC 是网卡的物理身份证（链路层、同一局域网内用）；IP 是逻辑门牌号（网络层、跨网络找路用）。数据包的两层头部各写各的。')
qa('ping 是什么原理？', 'ICMP 回显请求（type 8）+ 回显应答（type 0）。它测的是「一个来回的时间」，不建立连接（所以 ping 通不代表端口通）。')
qa('端口的作用？范围？', '区分同一台电脑上的不同程序（大楼的房间号）；0~65535，其中 1024 以下是众所周知的「服务端口」（80、443、53…）。')
qa('大端小端是什么？为什么要关心？', '多字节数字的两种存放顺序。网络协议规定用大端，x86 电脑是小端——直接按字节读会读反，必须手工转换，rd16/rd32 就是干这个的。')
qa('ARP 是干嘛的？', '在局域网里「用 IP 找 MAC」：广播问「谁是这个 IP」，持有者回自己的 MAC。以太网类型字段 0x0806（本项目目前只识别、没深入解析）。')

h2('F.3 项目相关（5 问）')
qa('讲一个你项目里遇到的「坑」。', '建议讲字节序：网络包按大端存，x86 是小端，直接强转数字会读反；解法是手工按字节拼，也就是 rd16/rd32。讲的时候顺手说说为什么不能图省事。')
qa('这个项目最难的部分是什么？', '可以答「把『边解析边打印』重构成『解析→档案袋→多方使用』」，因为这一步得停下来重新组织已有的代码，而不是往上加功能；讲到这里顺带就能说出 PacketInfo 的设计动机。')
qa('怎么保证代码的正确性？', '分层做：编译零警告；样例数据覆盖所有协议，六个包正好对应六种情况；每层都做边界检查；最后补一句「以后会给 parse_packet 写单元测试」，顺带说明你懂测试的价值。')
qa('这个项目还能怎么优化？', '提两个方向就够：①百万级包时，计数器表换哈希表、排序换快排；②大文件流式处理时把「全部打印」换成「抽样 + 统计」。注意强调「现在数据量小，不需要」。')
qa('做这个项目你学到了什么？', '挑真话讲：从「能写程序」到「知道为什么这么写」，具体就是设计决策、边界检查、可维护性这些；还有第一次完整走完 写代码→调试→版本管理→写文档 的流程。')

h2('F.4 git 相关（4 问）')
qa('commit 和 push 的区别？', 'commit 是本地存档（快照），push 是把存档上传到 GitHub。可以提交多次再一次性推送。')
qa('分支是干嘛的？你用了吗？', '分支 = 平行版本线，用来安全地做实验/多人协作。这个项目规模小，只用了 master 主线；但我了解标准流程是 feature 分支 → 合并。')
qa('改动错了怎么回退？', '还没提交：git checkout -- 文件 丢弃改动。已提交想撤销：git revert 生成一个「反向提交」（安全，历史可查）。避免用 reset 硬删历史。')
qa('.gitignore 是什么？你忽略了什么？', '告诉 git 哪些文件不用跟踪。本项目忽略了编译产物（packetlens、*.o）和 Python 缓存（__pycache__），原则是只存源码，能再生成的东西一律不进版本库。')

para('练习和面试题都过一遍，再回头看这个项目，你应该能把它从头讲清楚了。')

# ============================================================
# 附录 G
# ============================================================
h1('附录 G  英文词汇总表（界面上的每个字都看懂）')

para('这一份是「查字典」用的：以后在 GitHub 页面、代码、终端、网络资料里看到不认识的英文，先来这里找。按出现场景分成四组，每条 = 单词 · 中文意思 · 你在哪儿会碰到它。')

h2('G.1 GitHub 界面上的英文（按页面出现顺序）')
bullet('repository / repo · 仓库 · 项目在 GitHub 上的「家」，你的 packetlens 就是一个 repo')
bullet('owner · 所有者 · 仓库名前面那个账号名（Yui0818 / 里的前半截）')
bullet('Public / Private · 公开 / 私有 · 仓库可见性徽章；Public = 谁都能看')
bullet('Watch · 关注 · 按钮：订阅这个仓库的动态通知')
bullet('Star · 星标 · 像「点赞+收藏」，开源项目的人气数')
bullet('Fork · 派生（叉子）· 把别人的仓库复制一份到自己账号下再改')
bullet('Follow · 关注人 · 关注某个用户（不是仓库）')
bullet('Code · 代码 · 最大的标签页，放文件和下载按钮')
bullet('Issues · 问题单 · 提 bug / 记待办的地方')
bullet('Pull requests (PR) · 合并请求 · 别人改好了代码、请求合并进你的仓库')
bullet('Actions · 自动化 · 每次提交自动跑脚本（构建、测试）的地方')
bullet('Projects / Wiki · 看板 / 知识库 · 项目管理和文档页，小项目用不上')
bullet('Security · 安全 · 依赖漏洞告警')
bullet('Insights · 洞察 · 访问量、贡献者等统计数据')
bullet('Settings · 设置 · 改仓库名、公开私有、删除仓库（只有你自己能看）')
bullet('master / main · 主分支 · 代码的「主线」，选择器上那个默认名字')
bullet('branch · 分支 · 平行版本线，用来做实验或多人协作')
bullet('commit · 提交 · 一次代码快照；动词=拍快照')
bullet('Commits · 提交历史 · 点进去看每一次改动（有数字，比如 18 Commits）')
bullet('commit message · 提交说明 · 每张快照配的一句话，如「修个编译警告」')
bullet('hash · 哈希 · 提交的身份证号，一串字母数字（如 b4e6039）')
bullet('diff · 差异 · 提交详情页的红绿对比：绿色=新增行，红色=删除行')
bullet('Blame · 追责/溯源 · 文件页面里，看某一行是谁哪次提交写的')
bullet('clone · 克隆 · 把整个仓库连历史一起复制到本地（git clone 网址）')
bullet('Download ZIP · 下载压缩包 · 只要当前版本的快照，不带历史')
bullet('HTTPS / SSH · 两种连接方式 · clone 面板里切换用；HTTPS 用网址，SSH 用密钥')
bullet('Release · 发布版 · 给重要节点打正式版本号（如 v1.0）供人下载')
bullet('Package · 软件包 · 发布成可安装的包（pip/npm 那种），本项目不用')
bullet('Contributors · 贡献者 · 写过代码的人（本项目它显示 1 = 只有你自己）')
bullet('Languages · 语言构成 · 按文件字节统计的语言占比彩色条')
bullet('About · 关于 · 右栏：描述、协议、语言、人气数据的小结区')
bullet('Description · 描述 · 仓库的一句话简介（也可搜索到）')
bullet('Topics · 话题标签 · 给仓库贴的分类词，方便别人搜到')
bullet('License · 协议 · 授权条款；点开能读全文（我们选了 MIT）')
bullet('README · 读我 · 仓库首页自动展示的说明书（.md = Markdown 格式）')
bullet('Markdown · 标记语言 · 用 #、* 之类的符号写排版文字，GitHub 会渲染成好看的样子')
bullet('render · 渲染 · 把 Markdown 源码变成有样式页面的过程')
bullet('merge · 合并 · 把分支或 PR 的改动并进主线')
bullet('review / approve · 审阅 / 批准 · PR 流程里的两道关卡')

h2('G.2 C 语言关键字（课本和代码里最常撞见的 30 个）')
bullet('int · 整数类型 · 一般计数、下标用它（int i;）')
bullet('unsigned · 无符号（非负）· unsigned int 端口号、长度；unsigned char 单字节')
bullet('signed · 有符号（可正可负）· 默认就是它，一般不用写')
bullet('char · 字符/单字节 · char 就是 1 个字节；unsigned char 表示 0~255 的原始字节')
bullet('void · 空 · 「没有」：void 函数 = 不返回东西；void * = 任意类型指针')
bullet('const · 常量/只读 · 承诺不改它（我们的指针参数几乎都是 const）')
bullet('static · 静态/本文件私有 · 函数和全局变量加上它 = 外面看不见')
bullet('struct · 结构体 · 把多个变量捆成一捆（PacketInfo、Filter）')
bullet('typedef · 类型别名 · 给类型起短名字（typedef struct {...} PacketInfo;）')
bullet('union · 联合体 · 多个成员共用一块内存（本项目没用，先认得）')
bullet('enum · 枚举 · 给一组整数起名字（本项目没用，先认得）')
bullet('return · 返回 · 把结果交回给调用者，顺便结束函数')
bullet('if / else · 如果 / 否则 · 分支')
bullet('switch / case / default · 开关 / 情况 / 兜底 · 多分支（proto_name 用它）')
bullet('for · 循环（计数式）· for (i = 0; i < 6; i++) 搬字节')
bullet('while · 循环（条件式）· while (1) 一直转，靠 break 跳出')
bullet('do...while · 先做再判断的循环 · 本项目没用')
bullet('break · 打断 · 立刻退出整个循环/switch')
bullet('continue · 继续 · 这一轮跳过，下一轮接着来（live 模式等包时用它）')
bullet('goto · 跳转 · 跳到标签处（本项目的 push.bat 里用过同类思想；C 里不推荐常用）')
bullet('sizeof · 取大小 · 一个类型/变量占多少字节')
bullet('NULL · 空指针 · 「什么都没指」的指针（文件打不开时 fopen 返回 NULL）')
bullet('define · 定义 · #define MAX_ENTRIES 128 编译前替换的常量')
bullet('include · 引入 · #include <stdio.h> 把工具箱说明书引进来')
bullet('defined / ifdef · 已定义 / 条件编译 · 本项目没用（见过即可）')
bullet('main · 主函数 · 程序的入口，操作系统从这里开始跑')
bullet('argc / argv · 参数个数 / 参数内容 · 命令行的两个「传送门」')
bullet('pointer · 指针 · 存「地址」的变量（packet、info、f 都是）')
bullet('array · 数组 · 一排同类型的格子（mac_src[6]）')
bullet('buffer · 缓冲区 · 一块临时装数据的区域（errbuf 就是「错误消息筐」）')
bullet('bit / byte · 位 / 字节 · 1 字节 = 8 位；一个字节能存 0~255')
bullet('hexadecimal / hex · 十六进制 · 0x0800 这种写法；两个 hex 字符 = 一个字节')

h2('G.3 C 标准库常用函数（代码里遇到的都在这）')
bullet('printf / fprintf · 打印 · 前者到屏幕，后者到指定目的地（文件/屏幕）')
bullet('fopen / fclose · 打开文件 / 关闭文件 · 写报告三件套之首尾')
bullet('sscanf · 从字符串里按格式取数据 · 解析 "192.168.1.1" 用它')
bullet('atoi · 文字转整数 · atoi("80") → 80；非数字返回 0')
bullet('strcmp · 比较字符串 · 相等返回 0（对，0 才相等）')
bullet('strlen · 字符串长度 · 本项目没用（用 len 参数代替）')
bullet('memcpy / memset · 内存拷贝 / 内存填充 · 本项目没用（用循环 + {0} 代替）')
bullet('malloc / free · 申请内存 / 释放内存 · 本项目故意没用（见第 10.14 节）')
bullet('pcap_open_offline / pcap_open_live · 打开离线文件 / 打开网卡 · libpcap 的一对')
bullet('pcap_next_ex · 取下一个包 · 返回值 1=有包 0=超时 -1=错 -2=完')
bullet('pcap_close · 关闭抓包会话 · 打开的都要关')
bullet('pcap_datalink · 查链路层类型 · 判断是不是以太网（DLT_EN10MB）')

h2('G.4 终端与报错里的英文（看到别慌，对照着看）')
bullet('command · 命令 · 你敲的那一行指令')
bullet('argument · 参数 · 跟在命令后面的附加信息')
bullet('usage · 用法 · 程序告诉你该怎么用（我们没写参数时打印的就是它）')
bullet('command not found · 找不到这个命令 · 名字拼错 or 没装')
bullet('No such file or directory · 没有这个文件或目录 · 路径写错最常见')
bullet('Permission denied · 权限不够 · 抓包没加 sudo 就会见到它')
bullet('missing separator · 缺少分隔符 · Makefile 缩进用空格没 Tab 的经典报错')
bullet('warning / error · 警告 / 错误 · 警告可继续，错误必须改')
bullet('undefined reference · 未定义的引用 · 链接阶段找不到库（忘写 -lpcap）')
bullet('Segmentation fault (core dumped) · 段错误 · 读了不该读的内存，程序崩溃')
bullet('exit code / errorlevel · 退出码 · 0=成功，非 0=失败（push.bat 里判断用）')
bullet('root / sudo · 管理员 / 以管理员执行 · 抓网卡要它')
bullet('directory · 目录/文件夹 · cd 就是「换目录」')
bullet('execute / run · 执行 / 运行 · 跑程序')
bullet('compile / link · 编译 / 链接 · 翻译 + 接上库，两步合称构建（build）')
bullet('terminal / shell / bash · 终端 / 外壳 / 一种shell · 都在说你面前那个黑窗口')
bullet('process · 进程 · 正在运行的程序实例')
bullet('kill / Ctrl+C · 结束进程 / 中断 · 卡住时的救命操作')

h2('G.5 网络方向英文（看资料、文档时用）')
bullet('packet · 数据包 · 网络里流动的小包裹，本项目的主角')
bullet('capture · 抓取 · 抓包 = packet capture')
bullet('interface / device · 网卡/接口 · lo、eth0、any 都是「网卡名」')
bullet('promiscuous (mode) · 混杂模式 · 连不是发给本机的包也收')
bullet('offline / online · 离线 / 在线 · 读文件 vs 抓实时流量')
bullet('payload · 载荷 · 头部之后装的内容（数据本体）')
bullet('header · 头部 · 每层开头那几字节的「元信息」')
bullet('fragment · 分片 · 大包切成几块传输')
bullet('checksum · 校验和 · 防传输错误的「验算码」')
bullet('echo request / reply · 回显请求 / 应答 · ping 的一问一答')
bullet('handshake · 握手 · 建立连接前的确认流程（三次握手 = three-way handshake）')
bullet('session / connection · 会话 / 连接 · 一次完整的通信过程')
bullet('protocol · 协议 · 通信规则（TCP/UDP/ICMP/IP 都是）')
bullet('port · 端口 · 一栋楼里的房间号')
bullet('host · 主机 · 网络里的一台设备')
bullet('gateway · 网关 · 离开本局域网的「大门」（你家路由器）')
bullet('MAC address · MAC 地址 · 网卡身份证')
bullet('ethertype · 以太类型 · 以太网头里标明「里面是什么协议」的字段')
bullet('live capture · 实时抓取 · live 模式的英文说法')
bullet('trace / sniff · 追踪 / 嗅探 · 抓包的同义词，看到别懵')

para('到这里，该讲的都讲完了：从「不知道什么是文件」，到「界面每个词、代码每一行都能看懂」，再到「讲得出为什么、答得上面试题」。以后遇到新的英文词，就照附录 G 的样子记下来，写清楚它在哪儿出现，日子长了自然就熟了。')
