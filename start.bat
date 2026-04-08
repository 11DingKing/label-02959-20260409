@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo [信息] 线索池数据分割工具 — 启动中...

:: 检查 Python
set PYTHON=
for %%P in (python3 python) do (
    where %%P >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%V in ('%%P -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do (
            set PYTHON=%%P
            echo [完成] Python: %%V
            goto :found_python
        )
    )
)
echo [错误] 未找到 Python 3.9+，请安装: https://www.python.org/downloads/
pause
exit /b 1

:found_python

:: 虚拟环境
if not exist ".venv" (
    echo [信息] 创建虚拟环境...
    %PYTHON% -m venv .venv
)
call .venv\Scripts\activate.bat
echo [完成] 虚拟环境已激活

:: 安装依赖
echo [信息] 安装依赖...
pip install --upgrade pip -q 2>nul
pip install -r lead-splitter\requirements.txt -q
echo [完成] 依赖就绪

:: 生成测试数据
if not exist "lead-splitter\data\线索池_标准测试_100条.xlsx" (
    echo [信息] 生成测试数据...
    python lead-splitter\data\sample_leads.py
    echo [完成] 测试数据已生成
) else (
    echo [完成] 测试数据已存在
)

:: 启动桌面应用
echo.
echo ========================================
echo   线索池数据分割工具
echo ========================================
echo   关闭: 关闭窗口即可
echo.

cd lead-splitter
python main.py

pause
