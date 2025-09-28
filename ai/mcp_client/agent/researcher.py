# agents/researcher.py
from ..tools.search_tool import get_search_tool

async def researcher_node(state):
    tool = get_search_tool()
    result = await tool.ainvoke({
        "query": f"中国 {state['query']} 最新动态 发展趋势 数据"
    })

    content = "\n\n".join([r["content"] for r in result])
    urls = list(set([r["url"] for r in result]))

    return {
        "research_data": content,
        "sources": urls
    }
