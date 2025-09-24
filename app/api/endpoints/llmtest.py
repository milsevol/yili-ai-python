from fastapi import APIRouter,HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.services.langchain_service import get_langchain_client, convert_nl_to_es_query


router = APIRouter()

@router.get("/llm/test01")
async def llmttest01(question:str):
    client = get_langchain_client()
    chat_model = client["chat_model"]
    response = await chat_model.ainvoke(question)
    return response.content

@router.get("/llm/test02")
async def llmttest02(question:str):
    client = get_langchain_client()
    chat_model = client["chat_model"]
    
    async def generate_tokens():
        for response in chat_model.stream(question):
            if hasattr(response, 'content'):
                yield response.content
            else:
                yield str(response)
    
    return StreamingResponse(generate_tokens(), media_type="text/plain")