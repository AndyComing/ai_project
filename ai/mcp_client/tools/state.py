# state.py
from typing import TypedDict, List, Optional

class Trend(TypedDict):
    topic: str
    description: str
    data_support: str  # 支持该趋势的数据或案例

class MarketResearchState(TypedDict):
    query: str                    # 用户原始问题
    research_data: str            # 研究员收集的信息
    analysis: str                 # 分析师输出
    draft_report: str             # 初稿
    final_report: Optional[str]   # 最终报告
    trends: List[Trend]           # 结构化趋势列表
    sources: List[str]            # 来源链接
    revision_count: int           # 修改次数（防无限循环）
    feedback: str                 # 审核意见
