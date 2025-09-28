# langgraph/langgraph.py
from langgraph.graph import StateGraph, END
from .state import MarketResearchState
from ..agent.researcher import researcher_node
from ..agent.analyst import analyst_node
from ..agent.writer import writer_node
from ..agent.reviewer import reviewer_node

def build_graph():
    builder = StateGraph(MarketResearchState)

    # 添加节点
    builder.add_node("researcher", researcher_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("writer", writer_node)
    builder.add_node("reviewer", reviewer_node)

    # 设置起点
    builder.set_entry_point("researcher")

    # 连接流程
    builder.add_edge("researcher", "analyst")
    builder.add_edge("analyst", "writer")

    # 审核决策函数
    def should_review(state):
        if state["revision_count"] >= 2:
            return END  # 最多修改两次
        if "通过" in state["feedback"] or "合格" in state["feedback"]:
            return END
        return "reviewer"

    builder.add_conditional_edges("writer", should_review, {
        END: END,
        "reviewer": "reviewer"
    })
    builder.add_edge("reviewer", "writer")  # 审核后回到写作

    return builder.compile()
