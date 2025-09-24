from fastapi import APIRouter,HTTPException
router = APIRouter()

@router.get("/llm/test01")
async def llmttest01():
    return [
        {
            "id": "jj",
            "name": "tt"
        }
    ]