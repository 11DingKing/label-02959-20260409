"""
数据处理模块
负责 Excel/CSV 文件的读取、分析和分割导出
"""

import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict, Any
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class SplitConfig:
    """分割配置"""
    count: int  # 该份的数据条数
    filename: str  # 输出文件名


@dataclass
class DataStats:
    """数据统计信息"""
    total_rows: int
    wm_poi_id_count: int
    columns: List[str]
    analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "total_rows": self.total_rows,
            "wm_poi_id_count": self.wm_poi_id_count,
            "columns": self.columns,
        }
        if self.analysis:
            d["analysis"] = self.analysis
        return d


# 业务字段定义（来自 Prompt 需求）
BUSINESS_COLUMNS = {
    "wm_poi_id": "门店ID（必需）",
    "provider_id": "服务商ID",
    "lead_tag": "线索标签",
    "status": "状态",
    "modifier": "修改人",
}

# 日期字段可能的列名变体
DATE_COLUMN_PATTERNS = ["ctime", "date2datekey", "首次上线时间", "营业时间"]


class DataHandler:
    """数据处理器"""

    # 支持的文件格式
    SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv']

    # 必需的列
    REQUIRED_COLUMN = 'wm_poi_id'

    # 输出列映射
    OUTPUT_COLUMNS = {
        'wm_poi_id': '商家门店id',
        'provider_id': '服务商id'
    }

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._file_path: Optional[Path] = None
        logger.info("DataHandler 初始化完成")

    @property
    def is_loaded(self) -> bool:
        """是否已加载数据"""
        return self._df is not None

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """获取数据框"""
        return self._df

    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """加载文件"""
        logger.info(f"开始加载文件: {file_path}")
        path = Path(file_path)

        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False, f"文件不存在: {file_path}"

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            logger.error(f"不支持的文件格式: {suffix}")
            return False, f"不支持的文件格式: {suffix}，支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"

        try:
            if suffix == '.csv':
                for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.debug(f"CSV 文件使用编码: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("无法识别文件编码")
            else:
                df = pd.read_excel(file_path)

            if self.REQUIRED_COLUMN not in df.columns:
                logger.error(f"缺少必需列: {self.REQUIRED_COLUMN}, 现有列: {list(df.columns)}")
                return False, f"文件缺少必需列: {self.REQUIRED_COLUMN}"

            self._df = df
            self._file_path = path

            logger.info(f"成功加载文件: {file_path}, 共 {len(df)} 行数据, {len(df.columns)} 列")
            return True, f"成功加载 {len(df)} 条数据"

        except Exception as e:
            logger.exception(f"加载文件失败: {e}")
            return False, f"加载文件失败: {str(e)}"

    def validate_columns(self) -> Dict[str, Any]:
        """校验业务字段完整性，返回校验结果和警告"""
        if not self.is_loaded:
            return {"present": [], "missing": [], "warnings": [], "date_column": None}

        columns = [c.lower().strip() for c in self._df.columns]
        original_columns = list(self._df.columns)
        result = {
            "present": [],
            "missing": [],
            "warnings": [],
            "date_column": None,
        }

        for col, desc in BUSINESS_COLUMNS.items():
            if col in columns or col in original_columns:
                result["present"].append({"column": col, "description": desc})
            else:
                result["missing"].append({"column": col, "description": desc})
                if col != self.REQUIRED_COLUMN:
                    result["warnings"].append(f"缺少字段「{col}」({desc})")

        # 检测日期字段
        for pattern in DATE_COLUMN_PATTERNS:
            for orig_col in original_columns:
                if pattern.lower() in orig_col.lower():
                    result["date_column"] = orig_col
                    break
            if result["date_column"]:
                break

        return result

    def get_stats(self) -> Optional[DataStats]:
        """获取数据统计信息（含深度分析）"""
        if not self.is_loaded:
            return None

        df = self._df
        total_rows = len(df)
        wm_poi_id_count = df[self.REQUIRED_COLUMN].nunique()
        columns = list(df.columns)

        # 深度分析
        analysis = {}

        # provider_id 空值分析
        if "provider_id" in df.columns:
            empty_provider = df["provider_id"].isna() | (df["provider_id"].astype(str).str.strip() == "")
            analysis["provider_id_empty"] = int(empty_provider.sum())
            analysis["provider_id_filled"] = int(total_rows - empty_provider.sum())
        else:
            analysis["provider_id_empty"] = None

        # status 分布
        if "status" in df.columns:
            status_counts = df["status"].value_counts().to_dict()
            analysis["status_distribution"] = {str(k): int(v) for k, v in status_counts.items()}
        else:
            analysis["status_distribution"] = None

        # lead_tag 分布
        if "lead_tag" in df.columns:
            tag_counts = df["lead_tag"].value_counts().to_dict()
            analysis["lead_tag_distribution"] = {str(k): int(v) for k, v in tag_counts.items()}
        else:
            analysis["lead_tag_distribution"] = None

        # 日期范围分析
        date_col = None
        for pattern in DATE_COLUMN_PATTERNS:
            for col in df.columns:
                if pattern.lower() in col.lower():
                    date_col = col
                    break
            if date_col:
                break

        if date_col:
            try:
                col_data = df[date_col].dropna()
                # 检测是否为 Unix 时间戳（纯数字且范围合理：2000-01-01 ~ 2100-01-01）
                numeric = pd.to_numeric(col_data, errors="coerce").dropna()
                if len(numeric) > 0 and numeric.min() > 946684800 and numeric.max() < 4102444800:
                    dates = pd.to_datetime(numeric, unit="s", errors="coerce")
                else:
                    dates = pd.to_datetime(col_data, errors="coerce")
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    analysis["date_range"] = {
                        "column": date_col,
                        "earliest": str(valid_dates.min()),
                        "latest": str(valid_dates.max()),
                        "count": int(len(valid_dates)),
                    }
                else:
                    analysis["date_range"] = None
            except Exception:
                analysis["date_range"] = None
        else:
            analysis["date_range"] = None

        stats = DataStats(
            total_rows=total_rows,
            wm_poi_id_count=wm_poi_id_count,
            columns=columns,
            analysis=analysis,
        )

        logger.info(f"数据统计: 总行数={stats.total_rows}, wm_poi_id数量={stats.wm_poi_id_count}")
        return stats

    def get_preview(self, rows: int = 10) -> Optional[pd.DataFrame]:
        """获取数据预览"""
        if not self.is_loaded:
            return None
        return self._df.head(rows)

    def validate_split_config(self, configs: List[SplitConfig]) -> Tuple[bool, str]:
        """验证分割配置"""
        logger.info(f"开始验证分割配置, 共 {len(configs)} 份")

        if not self.is_loaded:
            logger.warning("验证失败: 数据未加载")
            return False, "请先导入数据文件"

        if not configs:
            logger.warning("验证失败: 配置为空")
            return False, "请至少配置一份分割"

        for i, config in enumerate(configs):
            if not config.filename.strip():
                logger.warning(f"验证失败: 第 {i + 1} 份文件名为空")
                return False, f"第 {i + 1} 份的文件名不能为空"

        filenames = [c.filename.strip() for c in configs]
        if len(filenames) != len(set(filenames)):
            logger.warning(f"验证失败: 文件名重复, {filenames}")
            return False, "文件名不能重复"

        total_config = sum(c.count for c in configs)
        total_data = len(self._df)

        if total_config != total_data:
            logger.warning(f"验证失败: 配置总数 {total_config} != 数据总数 {total_data}")
            return False, f"配置总数 ({total_config}) 与数据总数 ({total_data}) 不匹配"

        for i, config in enumerate(configs):
            if config.count <= 0:
                logger.warning(f"验证失败: 第 {i + 1} 份数量 <= 0")
                return False, f"第 {i + 1} 份的数量必须大于 0"

        logger.info("分割配置验证通过")
        return True, "配置验证通过"

    def split_and_export(
        self,
        configs: List[SplitConfig],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[bool, str, List[str]]:
        """分割并导出数据"""
        logger.info(f"开始分割导出, 输出目录: {output_dir}")

        valid, msg = self.validate_split_config(configs)
        if not valid:
            return False, msg, []

        output_path = Path(output_dir)

        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception(f"创建输出目录失败: {e}")
            return False, f"创建输出目录失败: {str(e)}", []

        output_files = []
        current_index = 0
        total_parts = len(configs)

        try:
            for i, config in enumerate(configs):
                logger.info(f"正在导出第 {i + 1}/{total_parts} 份: {config.filename}, 数量: {config.count}")

                if progress_callback:
                    progress_callback(i, total_parts, f"正在导出第 {i + 1} 份: {config.filename}")

                end_index = current_index + config.count
                slice_df = self._df.iloc[current_index:end_index].copy()

                output_df = pd.DataFrame()
                output_df['商家门店id'] = slice_df[self.REQUIRED_COLUMN]
                output_df['服务商id'] = ''

                filename = config.filename.strip()
                if not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                output_file = output_path / filename

                output_df.to_excel(output_file, index=False, engine='openpyxl')
                output_files.append(str(output_file))

                logger.info(f"导出完成: {output_file}, 共 {len(output_df)} 条数据")

                current_index = end_index

            if progress_callback:
                progress_callback(total_parts, total_parts, "导出完成")

            logger.info(f"全部导出完成, 共 {len(configs)} 个文件")
            return True, f"成功导出 {len(configs)} 个文件", output_files

        except Exception as e:
            logger.exception(f"导出失败: {e}")
            return False, f"导出失败: {str(e)}", output_files

    def clear(self):
        """清除已加载的数据"""
        self._df = None
        self._file_path = None
        logger.info("数据已清除")
