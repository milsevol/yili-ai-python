import asyncio
import pytest
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query

@pytest.mark.asyncio
async def test_es_query():
    try:
        client = get_langchain_client()
        print('LangChain客户端创建成功')
        result = await convert_nl_to_es_query('查找所有关于投资理财的对话', client)
        print('查询结果:', result)
        assert isinstance(result, dict), "查询结果应该是一个字典"
        assert "query" in result, "查询结果应该包含query字段"
        assert "highlight" in result, "查询结果应该包含highlight字段"
        return result
    except Exception as e:
        print(f'发生错误: {str(e)}')
        raise

if __name__ == '__main__':
    asyncio.run(test_es_query())