from typing import Any

from fastapi import APIRouter
from Utils.Utils import get_vector_store

chatRoute = APIRouter(tags=["ChatAPI"])

@chatRoute.get("/")
async def get_chat(query: str) -> Any:
    vector_store = get_vector_store()
    docs = vector_store.similarity_search_with_score(query, k=3)

    data_return = []
    for doc in docs:
        data_return.append([str(doc[0].page_content), doc[1]])
    return data_return







