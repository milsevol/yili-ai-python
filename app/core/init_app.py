from app.services.es_service import get_es_client, create_conversation_index

# 初始化应用
def init_app():
    # 初始化Elasticsearch索引
    try:
        es_client = get_es_client()
        create_conversation_index(es_client)
        print("Elasticsearch索引初始化成功")
    except Exception as e:
        print(f"Elasticsearch索引初始化失败: {str(e)}")