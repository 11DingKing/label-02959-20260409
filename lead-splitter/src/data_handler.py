"""
数据处理模块
负责 Excel/CSV 文件的读取、分析和分割导出
"""

import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .logger import get_logger

logger = get_logger(__name__)


# 尝试导入 Qt 模块，如果失败则使用备用方案
try:
    from PyQt6.QtCore import QObject, pyqtSignal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    
    # 定义备用的 QObject 和 pyqtSignal
    class QObject:
        """备用 QObject 类，用于非 Qt 环境"""
        pass
    
    def pyqtSignal(*args, **kwargs):
        """备用 pyqtSignal 装饰器，用于非 Qt 环境"""
        class Signal:
            def __init__(self):
                self._callbacks = []
            
            def connect(self, callback):
                self._callbacks.append(callback)
            
            def emit(self, *args, **kwargs):
                for callback in self._callbacks:
                    try:
                        callback(*args, **kwargs)
                    except Exception:
                        pass
        
        return Signal()


# Unix 时间戳检测范围常量
# 2000-01-01 00:00:00 UTC 的 Unix 时间戳
TIMESTAMP_MIN_SECONDS = 946684800
# 2100-01-01 00:00:00 UTC 的 Unix 时间戳
TIMESTAMP_MAX_SECONDS = 4102444800
# 毫秒级时间戳阈值（超过此值视为毫秒级）
TIMESTAMP_MILLISECONDS_THRESHOLD = 10**12
# 微秒级时间戳阈值（超过此值视为微秒级）
TIMESTAMP_MICROSECONDS_THRESHOLD = 10**15


class SplitMode(Enum):
    """分割模式枚举"""
    EXACT = "精确分配"
    PARTIAL = "部分导出"
    RATIO = "按比例分配"


@dataclass
class SplitConfig:
    """分割配置"""
    count: int  # 该份的数据条数
    filename: str  # 输出文件名
    ratio: Optional[float] = None  # 按比例分配时的比例（0-1之间）


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


@dataclass
class ExportPreview:
    """导出预览信息"""
    total_rows: int
    columns: List[str]
    groups: List[Dict[str, Any]] = field(default_factory=list)
    sample_data: List[Dict[str, Any]] = field(default_factory=list)


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


class DataHandler(QObject):
    """数据处理器"""

    # 进度信号：(current, total, message)
    if QT_AVAILABLE:
        progress = pyqtSignal(int, int, str)
    else:
        progress = pyqtSignal()

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
        super().__init__()
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

    def _normalize_timestamp(self, value: float) -> float:
        """
        标准化时间戳，自动识别秒、毫秒、微秒级时间戳
        返回秒级时间戳
        """
        if value >= TIMESTAMP_MICROSECONDS_THRESHOLD:
            return value / 1000000
        elif value >= TIMESTAMP_MILLISECONDS_THRESHOLD:
            return value / 1000
        return value

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
                if len(numeric) > 0:
                    # 标准化时间戳（自动识别秒、毫秒、微秒）
                    normalized_numeric = numeric.apply(self._normalize_timestamp)
                    # 检查是否在合理范围内
                    if normalized_numeric.min() > TIMESTAMP_MIN_SECONDS and normalized_numeric.max() < TIMESTAMP_MAX_SECONDS:
                        dates = pd.to_datetime(normalized_numeric, unit="s", errors="coerce")
                    else:
                        dates = pd.to_datetime(col_data, errors="coerce")
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

    def _calculate_ratio_counts(self, configs: List[SplitConfig], total_rows: int) -> List[SplitConfig]:
        """
        根据比例计算实际条数
        余数分给最后一组
        """
        calculated_configs = []
        total_ratio = sum(c.ratio for c in configs if c.ratio is not None)
        
        # 如果比例总和不为1，按比例分配
        allocated = 0
        for i, config in enumerate(configs):
            if config.ratio is not None:
                if i == len(configs) - 1:
                    # 最后一组分配剩余的
                    count = total_rows - allocated
                else:
                    count = int(total_rows * (config.ratio / total_ratio))
                    allocated += count
            else:
                count = config.count
            
            calculated_configs.append(SplitConfig(
                count=count,
                filename=config.filename,
                ratio=config.ratio
            ))
        
        return calculated_configs

    def _validate_split_config_internal(
        self, 
        configs: List[SplitConfig], 
        mode: SplitMode = SplitMode.EXACT
    ) -> Tuple[bool, str, List[SplitConfig]]:
        """
        内部验证分割配置方法
        支持三种模式：
        - EXACT: 精确分配（总数必须相等）
        - PARTIAL: 部分导出（配置总数小于数据总数，剩余的导出到"未分配"文件）
        - RATIO: 按比例分配（配置项填百分比而不是绝对数量）
        
        返回: (是否有效, 消息, 计算后的配置列表)
        """
        logger.info(f"开始验证分割配置, 共 {len(configs)} 份, 模式: {mode.value}")

        if not self.is_loaded:
            logger.warning("验证失败: 数据未加载")
            return False, "请先导入数据文件", []

        if not configs:
            logger.warning("验证失败: 配置为空")
            return False, "请至少配置一份分割", []

        for i, config in enumerate(configs):
            if not config.filename.strip():
                logger.warning(f"验证失败: 第 {i + 1} 份文件名为空")
                return False, f"第 {i + 1} 份的文件名不能为空", []

        filenames = [c.filename.strip() for c in configs]
        if len(filenames) != len(set(filenames)):
            logger.warning(f"验证失败: 文件名重复, {filenames}")
            return False, "文件名不能重复", []

        total_data = len(self._df)
        calculated_configs = configs

        if mode == SplitMode.RATIO:
            # 按比例分配模式
            for i, config in enumerate(configs):
                if config.ratio is None:
                    logger.warning(f"验证失败: 第 {i + 1} 份未设置比例")
                    return False, f"按比例分配模式下，第 {i + 1} 份必须设置比例", []
                if config.ratio <= 0 or config.ratio > 1:
                    logger.warning(f"验证失败: 第 {i + 1} 份比例无效")
                    return False, f"第 {i + 1} 份的比例必须在 (0, 1] 之间", []
            
            # 计算实际条数
            calculated_configs = self._calculate_ratio_counts(configs, total_data)
            total_config = sum(c.count for c in calculated_configs)
            
            # 验证计算后的总数
            if total_config != total_data:
                logger.warning(f"验证失败: 计算后总数 {total_config} != 数据总数 {total_data}")
                return False, f"比例计算后总数 ({total_config}) 与数据总数 ({total_data}) 不匹配", []
            
            # 验证每条配置的数量
            for i, config in enumerate(calculated_configs):
                if config.count <= 0:
                    logger.warning(f"验证失败: 第 {i + 1} 份数量 <= 0")
                    return False, f"第 {i + 1} 份的数量必须大于 0", []
        
        else:
            # 精确分配或部分导出模式
            total_config = sum(c.count for c in configs)
            
            for i, config in enumerate(configs):
                if config.count <= 0:
                    logger.warning(f"验证失败: 第 {i + 1} 份数量 <= 0")
                    return False, f"第 {i + 1} 份的数量必须大于 0", []
            
            if mode == SplitMode.EXACT:
                if total_config != total_data:
                    logger.warning(f"验证失败: 配置总数 {total_config} != 数据总数 {total_data}")
                    return False, f"配置总数 ({total_config}) 与数据总数 ({total_data}) 不匹配", []
            elif mode == SplitMode.PARTIAL:
                if total_config > total_data:
                    logger.warning(f"验证失败: 配置总数 {total_config} > 数据总数 {total_data}")
                    return False, f"配置总数 ({total_config}) 不能大于数据总数 ({total_data})", []
                
                # 添加未分配组
                unallocated_count = total_data - total_config
                if unallocated_count > 0:
                    calculated_configs = configs.copy()
                    calculated_configs.append(SplitConfig(
                        count=unallocated_count,
                        filename="未分配",
                        ratio=None
                    ))

        logger.info("分割配置验证通过")
        return True, "配置验证通过", calculated_configs

    def validate_split_config(self, configs: List[SplitConfig]) -> Tuple[bool, str]:
        """
        验证分割配置（向后兼容版本）
        使用精确分配模式，只返回 (是否有效, 消息)
        
        返回: (是否有效, 消息)
        """
        valid, msg, _ = self._validate_split_config_internal(configs, SplitMode.EXACT)
        return valid, msg

    def validate_split_config_with_mode(
        self, 
        configs: List[SplitConfig], 
        mode: SplitMode = SplitMode.EXACT
    ) -> Tuple[bool, str, List[SplitConfig]]:
        """
        验证分割配置（支持新模式）
        支持三种模式：
        - EXACT: 精确分配（总数必须相等）
        - PARTIAL: 部分导出（配置总数小于数据总数，剩余的导出到"未分配"文件）
        - RATIO: 按比例分配（配置项填百分比而不是绝对数量）
        
        返回: (是否有效, 消息, 计算后的配置列表)
        """
        return self._validate_split_config_internal(configs, mode)

    def get_export_preview(
        self, 
        configs: List[SplitConfig], 
        mode: SplitMode = SplitMode.EXACT
    ) -> Tuple[bool, str, Optional[ExportPreview]]:
        """
        获取导出预览
        在真正导出之前先生成一个摘要（每组的条数、字段列表、前3条数据预览）
        
        返回: (是否成功, 消息, 预览信息)
        """
        logger.info("开始生成导出预览")

        # 先验证配置
        valid, msg, calculated_configs = self._validate_split_config_internal(configs, mode)
        if not valid:
            return False, msg, None

        if not self.is_loaded:
            return False, "请先导入数据文件", None

        df = self._df
        total_rows = len(df)
        columns = list(df.columns)

        # 生成各组信息
        groups = []
        current_index = 0
        for config in calculated_configs:
            end_index = current_index + config.count
            slice_df = df.iloc[current_index:end_index]
            
            # 获取前3条数据预览
            sample_rows = []
            for _, row in slice_df.head(3).iterrows():
                sample_row = {}
                for col in columns:
                    sample_row[col] = row[col]
                sample_rows.append(sample_row)
            
            groups.append({
                "filename": config.filename,
                "count": config.count,
                "sample_data": sample_rows
            })
            
            current_index = end_index

        # 获取整体前3条数据预览
        overall_sample = []
        for _, row in df.head(3).iterrows():
            sample_row = {}
            for col in columns:
                sample_row[col] = row[col]
            overall_sample.append(sample_row)

        preview = ExportPreview(
            total_rows=total_rows,
            columns=columns,
            groups=groups,
            sample_data=overall_sample
        )

        logger.info("导出预览生成完成")
        return True, "预览生成成功", preview

    def _emit_progress(self, current: int, total: int, message: str):
        """
        发射进度信号
        同时调用回调函数（保持向后兼容）
        """
        # 发射 Qt 信号
        try:
            self.progress.emit(current, total, message)
        except Exception:
            # 如果信号连接失败，忽略错误
            pass
        
        logger.debug(f"进度: {current}/{total} - {message}")

    def split_and_export(
        self,
        configs: List[SplitConfig],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        mode: SplitMode = SplitMode.EXACT,
        preserve_all_columns: bool = False
    ) -> Tuple[bool, str, List[str]]:
        """
        分割并导出数据
        
        参数:
            configs: 分割配置列表
            output_dir: 输出目录
            progress_callback: 进度回调函数（保持向后兼容）
            mode: 分割模式（默认精确分配）
            preserve_all_columns: 是否保留所有原始字段（默认False，保持向后兼容）
        
        向后兼容行为（preserve_all_columns=False）:
            - 只导出 wm_poi_id 和 provider_id 两列
            - 列名映射为 '商家门店id' 和 '服务商id'
            - provider_id 列为空
        
        新行为（preserve_all_columns=True）:
            - 保留所有原始字段
            - 在每条记录末尾追加一个"分配组"列标明属于哪个分割组
            - 导出的 Excel 文件第一行要有表头
        
        进度更新:
            - 通过 Qt 信号槽机制发射进度信号
            - 同时支持 progress_callback 回调函数（保持向后兼容）
        """
        logger.info(f"开始分割导出, 输出目录: {output_dir}, 模式: {mode.value}")

        # 验证配置并获取计算后的配置
        valid, msg, calculated_configs = self._validate_split_config_internal(configs, mode)
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
        total_parts = len(calculated_configs)

        try:
            for i, config in enumerate(calculated_configs):
                logger.info(f"正在导出第 {i + 1}/{total_parts} 份: {config.filename}, 数量: {config.count}")

                # 发射进度信号
                message = f"正在导出第 {i + 1} 份: {config.filename}"
                self._emit_progress(i, total_parts, message)
                
                # 同时调用回调函数（保持向后兼容）
                if progress_callback:
                    progress_callback(i, total_parts, message)

                end_index = current_index + config.count
                slice_df = self._df.iloc[current_index:end_index].copy()

                if preserve_all_columns:
                    # 新行为：保留所有原始字段，添加"分配组"列
                    output_df = slice_df.copy()
                    output_df['分配组'] = config.filename
                else:
                    # 向后兼容行为：只导出指定列
                    output_df = pd.DataFrame()
                    output_df['商家门店id'] = slice_df[self.REQUIRED_COLUMN]
                    output_df['服务商id'] = ''

                filename = config.filename.strip()
                if not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                output_file = output_path / filename

                # 导出时包含表头
                output_df.to_excel(output_file, index=False, engine='openpyxl', header=True)
                output_files.append(str(output_file))

                logger.info(f"导出完成: {output_file}, 共 {len(output_df)} 条数据")

                current_index = end_index

            # 发射完成信号
            self._emit_progress(total_parts, total_parts, "导出完成")
            
            # 同时调用回调函数（保持向后兼容）
            if progress_callback:
                progress_callback(total_parts, total_parts, "导出完成")

            logger.info(f"全部导出完成, 共 {len(calculated_configs)} 个文件")
            return True, f"成功导出 {len(calculated_configs)} 个文件", output_files

        except Exception as e:
            logger.exception(f"导出失败: {e}")
            return False, f"导出失败: {str(e)}", output_files

    def clear(self):
        """清除已加载的数据"""
        self._df = None
        self._file_path = None
        logger.info("数据已清除")
