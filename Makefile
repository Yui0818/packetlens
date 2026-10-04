# Makefile：告诉编译器"怎么把我的代码变成可执行程序"
#
# 运行方式：在项目目录里输入  make
#   它会自动编译 src/main.c 生成名为 packetlens 的可执行程序。
# 运行方式：make clean
#   它会删掉编译出来的 packetlens，清理干净。

# CC 是"用哪个编译器"。gcc 是 GNU C 编译器（你 WSL 里的那个）。
CC = gcc

# CFLAGS 是"编译选项"。
#   -Wall   : 把常见的警告都打开（写错了会提醒你）
#   -Wextra : 更严格一点的警告
#   -O2     : 二级优化，跑得更快
CFLAGS = -Wall -Wextra -O2

# LIBS 是"链接库"。我们要用 libpcap，所以要 -lpcap。
LIBS = -lpcap

# all 是默认目标。make 不带参数时会执行它。
all: packetlens

# 这一行是"编译规则"：
#   packetlens 由 src/main.c 生成
#   $(CC) ... : 用编译器执行
#   -o packetlens : 输出文件名叫 packetlens
#   $(LIBS)     : 链接 libpcap
packetlens: src/main.c
	$(CC) $(CFLAGS) -o packetlens src/main.c $(LIBS)

# clean 用来清理。
clean:
	rm -f packetlens

# .PHONY 声明这些目标不是"真实文件"，避免冲突。
.PHONY: all clean
