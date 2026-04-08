#!/usr/bin/env bash
# ============================================================
# 线索池数据分割工具 — 一键启动脚本
# 兼容 macOS / Linux / Windows (Git Bash)
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[信息]${NC} $1"; }
ok()    { echo -e "${GREEN}[完成]${NC} $1"; }
warn()  { echo -e "${YELLOW}[警告]${NC} $1"; }
fail()  { echo -e "${RED}[错误]${NC} $1"; exit 1; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

OS="unknown"
case "$(uname -s)" in
    Darwin*)  OS="mac";;
    Linux*)   OS="linux";;
    MINGW*|MSYS*|CYGWIN*) OS="win";;
esac
info "系统: $OS"

# ============================================================
# 1. 检查 Python 3.9+
# ============================================================
PYTHON=""

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
                PYTHON="$cmd"
                return 0
            fi
        fi
    done
    return 1
}

if ! find_python; then
    warn "未找到 Python 3.9+，尝试自动安装..."
    if [ "$OS" = "mac" ]; then
        if command -v brew &>/dev/null; then
            brew install python@3.11
        else
            fail "请先安装 Homebrew 或手动安装 Python 3.9+"
        fi
    elif [ "$OS" = "linux" ]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3 python3-pip
        else
            fail "请手动安装 Python 3.9+"
        fi
    else
        fail "请安装 Python 3.9+: https://www.python.org/downloads/"
    fi
    find_python || fail "Python 安装失败"
fi
ok "Python: $($PYTHON --version)"

# ============================================================
# 2. 虚拟环境 & 依赖
# ============================================================
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    info "创建虚拟环境..."
    $PYTHON -m venv "$VENV_DIR"
fi

if [ "$OS" = "win" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    source "$VENV_DIR/bin/activate"
fi
ok "虚拟环境已激活"

info "安装依赖..."
pip install --upgrade pip -q 2>/dev/null
pip install -r lead-splitter/requirements.txt -q
ok "依赖就绪"

# ============================================================
# 3. 生成测试数据
# ============================================================
if [ ! -f "lead-splitter/data/线索池_标准测试_100条.xlsx" ]; then
    info "生成测试数据..."
    python lead-splitter/data/sample_leads.py
    ok "测试数据已生成"
else
    ok "测试数据已存在"
fi

# ============================================================
# 4. 启动桌面应用
# ============================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  线索池数据分割工具${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  关闭: ${YELLOW}Ctrl+C 或关闭窗口${NC}"
echo ""

cd lead-splitter
python main.py
