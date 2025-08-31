import asyncio
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query

async def test():
    try:
        client = get_langchain_client()
        print('LangChain客户端创建成功')
        result = await convert_nl_to_es_query('查找所有关于投资理财的对话', client)
        print('查询结果:', result)
    except Exception as e:
        print(f'发生错误: {str(e)}')

if __name__ == '__main__':
    asyncio.run(test())