#!/usr/bin/env python3
"""
测试运行脚本
"""

import subprocess
import sys
from pathlib import Path


def main():
    """运行所有测试"""
    project_dir = Path(__file__).parent
    
    print("=" * 60)
    print("线索池数据分割工具 - 测试套件")
    print("=" * 60)
    
    # 运行 pytest
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(project_dir / "tests"),
            "-v",
            "--tb=short",
            "-x",  # 遇到第一个失败就停止
        ],
        cwd=str(project_dir)
    )
    
    print("=" * 60)
    if result.returncode == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 测试失败!")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
