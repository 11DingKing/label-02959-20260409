# 线索池数据分割工具

Python 桌面工具，用于线索池 Excel/CSV 数据的分析与分割导出。单进程本地 PyQt6 GUI，直接处理数据。

---

## How to Run

### 一键启动（推荐）

```bash
# macOS / Linux
./start.sh

# Windows（双击或命令行）
start.bat
```

脚本自动完成以下步骤：
1. 检查 Python 3.9+（未安装则尝试自动安装）
2. 创建虚拟环境 `.venv`，安装依赖
3. 生成中文测试数据（首次运行）
4. 启动桌面 GUI

### 前置要求

- Python 3.9+

### 手动启动

```bash
# 1. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r lead-splitter/requirements.txt

# 3. 生成测试数据（首次）
python lead-splitter/data/sample_leads.py

# 4. 启动
cd lead-splitter && python main.py
```

---

## 测试账号

本工具为本地桌面应用，无需账号登录。

---

## 题目内容

用 Python 做一个工具，窗口化，有进度条。

**线索池字段：**
- wm_poi_id
- provider_id
- lead_tag
- status
- modifier
- `date2datekey`(`from_unixtime`(`a`.`ctime`)) 首次上线时间或营业时间

**功能需求：**
1. 导入线索池，分析表格有多少条 wm_poi_id 数据
2. 需要分割成多少份，一份多少条可以选择
3. 分割成 N 份，每份可设置条数和文件名
4. 总数对应总表格的数量即可分割
5. 分割出来的表格保存：商家门店id（对应 wm_poi_id）、服务商id（留空）

---

## 功能特性

- 支持 Excel（.xlsx / .xls）和 CSV 格式导入
- 自动检测文件编码（UTF-8 / GBK / GB2312）
- 业务字段完整性校验（wm_poi_id、provider_id、lead_tag、status、modifier）
- 深度数据分析：服务商ID空值统计、状态分布、时间范围（自动识别 Unix 时间戳）、字段完整度
- 自定义分割份数、每份条数、文件名，支持平均分配
- 导出为标准格式（商家门店id + 服务商id）
- Toast 应用内通知（成功 / 警告 / 错误 / 信息）
- Element Plus 风格 UI，PingFang SC 字体，卡片阴影布局

---

## 测试数据

位于 `lead-splitter/data/`，由 `sample_leads.py` 自动生成，包含真实中文内容：

| 文件名 | 数据量 | 用途 |
|--------|--------|------|
| 线索池_小型测试_50条.xlsx | 50 条 | 快速验证 |
| 线索池_标准测试_100条.xlsx | 100 条 | 标准测试 |
| 线索池_大型测试_500条.xlsx | 500 条 | 性能测试 |
| 线索池_CSV格式_100条.csv | 100 条 | CSV 兼容性 |

---

## 运行测试

```bash
source .venv/bin/activate
python -m pytest lead-splitter/tests/ -v
```

---

## 项目结构

```
├── start.sh / start.bat        # 一键启动脚本
├── README.md
└── lead-splitter/              # PyQt6 桌面应用
    ├── main.py                 # 启动入口
    ├── requirements.txt
    ├── data/                   # 测试数据（中文）
    │   └── sample_leads.py     # 数据生成脚本
    ├── src/
    │   ├── app.py              # 应用入口
    │   ├── main_window.py      # 主窗口（统计卡片 + 深度分析）
    │   ├── data_handler.py     # 数据处理（加载 / 校验 / 分析 / 分割导出）
    │   ├── widgets.py          # 自定义组件（StatCard / SplitPartWidget）
    │   ├── styles.py           # 样式（Element Plus 风格）
    │   ├── toast.py            # Toast 应用内通知
    │   └── logger.py           # 日志
    └── tests/                  # 测试
        ├── conftest.py         # 共享 fixtures
        ├── test_data_handler.py # 数据处理测试
        ├── test_integration.py  # 集成测试
        └── test_widgets.py      # 组件测试
```

---

## 技术栈

- Python 3.9+
- GUI：PyQt6
- 数据处理：pandas + openpyxl
- 测试：pytest + pytest-qt
