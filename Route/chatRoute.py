from typing import Any
from langchain.llms import HuggingFaceHub
from fastapi import APIRouter, Depends

from Controller.authController import AuthController
from Utils.Utils import get_vector_store, get_conversational_rag_chain, get_retriever


chatRoute = APIRouter(tags=["ChatAPI"])


@chatRoute.get("/")
async def get_chat(
        query: str = "",
        decoded_token = Depends(AuthController())
) -> Any:
    session_id = decoded_token["id"]
    conversational_rag_chain = get_conversational_rag_chain()
    answer = conversational_rag_chain.invoke(
        {"input": query},
        config={
            "configurable": {"session_id": session_id}
        },  # constructs a key "abc123" in `store`.
    )["answer"]

    return answer












