from ollama import chat


MODEL_NAME = "qwen3:8b"


SYSTEM_PROMPT = """
You are CloudRAG, a document-grounded AI assistant.

Your job is to answer questions using ONLY the provided
document context.

Rules:

1. Use the provided context as your primary source of truth.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information to answer
   the question, clearly say that the information was not found
   in the provided documents.
4. Give concise but useful answers.
5. When appropriate, mention which source document supports the answer.
6. Do not pretend that information exists in the documents when it does not.
"""


def generate_answer(
    question: str,
    context: str,
) -> str:

    prompt = f"""
DOCUMENT CONTEXT:

{context}

USER QUESTION:

{question}

Answer the user's question using the document context above.
"""

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response["message"]["content"]