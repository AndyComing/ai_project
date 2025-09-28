# tools/search_tool.py
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
    
    def get_search_tool():
        return TavilySearchResults(
            max_results=6,
            include_domains=["zhihu.com", "sohu.com", "eastmoney.com", "cnblogs.com"],
            exclude_domains=["youtube.com", "twitter.com"]
        )
except ImportError:
    # 如果 TavilySearchResults 不可用，提供一个模拟的搜索工具
    def get_search_tool():
        class MockSearchTool:
            async def ainvoke(self, query):
                return [
                    {
                        "content": f"基于查询 '{query['query']}' 的模拟搜索结果",
                        "url": "https://example.com"
                    }
                ]
        return MockSearchTool()
