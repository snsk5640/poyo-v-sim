# Makefile for poyo-v-sim using Icarus Verilog

# -------------------------------------
# 設定
# -------------------------------------
# ソースコードのあるディレクトリ
SRC_DIR = ../src/pipeline_3stage/design

# コンパイル対象のソースファイル（すべての.vファイルを指定）
SRCS = $(wildcard $(SRC_DIR)/*.v)

# 生成する実行ファイル名
TARGET = poyo_sim.out

# 生成する波形ファイル名
VCD_FILE = wave.vcd

# トップモジュール名（cpu_tb.vの中のモジュール名と合わせる）
# ※通常はファイル名と同じ cpu_tb だと思われます
TOP_MODULE = cpu_tb

# -------------------------------------
# ツール
# -------------------------------------
IV = iverilog
VVP = vvp
GTKWAVE = gtkwave

# コンパイルフラグ
# -I : インクルードファイルの検索パス（define.vhのため）
# -D : マクロ定義（必要なら追加、例: -DICARUS_VERILOG）
FLAGS = -I $(SRC_DIR) -s $(TOP_MODULE)

# -------------------------------------
# コマンド
# -------------------------------------
all: build run

# コンパイル
build: $(TARGET)

$(TARGET): $(SRCS)
	@echo "Compiling..."
	$(IV) $(FLAGS) -o $(TARGET) $(SRCS)

# シミュレーション実行
run: $(TARGET)
	@echo "Running simulation..."
	$(VVP) $(TARGET)

# 波形表示
wave:
	@if [ -f $(VCD_FILE) ]; then \
		echo "Opening waveform..."; \
		$(GTKWAVE) $(VCD_FILE); \
	else \
		echo "Error: $(VCD_FILE) not found. Run 'make run' first."; \
	fi

# クリーンアップ
clean:
	rm -f $(TARGET) $(VCD_FILE)

.PHONY: all build run wave clean
