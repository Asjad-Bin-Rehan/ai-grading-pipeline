from typing import List

from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..config import settings
from .chat_tools import CHAT_TOOLS

SYSTEM_PROMPT = """You are an AI grading assistant for professors using the AI Grading Pipeline.

You help professors:
- Grade all quizzes in a folder using grade_quizzes_from_folder (e.g. "samples/generated")
- List quiz files in a folder using list_quizzes_in_folder
- Review grading results and statistics
- Find students flagged for human review
- Look up detailed scores and per-question feedback
- Check status of background grading tasks by task_id
- See what files have been uploaded recently

Important:
- When the user asks to grade quizzes in a folder, call list_quizzes_in_folder first if needed, then grade_quizzes_from_folder.
- Grading runs in the background via Celery. After queuing, tell the user how many tasks were queued and that results appear in the Results dashboard.
- Always use tools to fetch real data before answering questions about grades.
- Be concise, clear, and professional.
- When showing scores, mention if a student needs human review.
"""

def _build_chat_model():
    provider = settings.model_provider.lower()

    if provider == 'groq':
        if not settings.groq_api_key:
            raise RuntimeError('GROQ_API_KEY is not configured for the chat agent')
        model_name = settings.groq_model or 'llama-3.3-70b-versatile'
        return ChatGroq(model=model_name, temperature=0, groq_api_key=settings.groq_api_key)

    if provider == 'openai':
        if not settings.openai_api_key:
            raise RuntimeError('OPENAI_API_KEY is not configured for the chat agent')
        return ChatOpenAI(model='gpt-4.1-mini', temperature=0, api_key=settings.openai_api_key)

    if provider in ('mock', 'demo', 'local'):
        if not settings.groq_api_key and not settings.openai_api_key:
            raise RuntimeError(
                'Chat agent requires GROQ_API_KEY or OPENAI_API_KEY. Set MODEL_PROVIDER=groq or openai.'
            )
        if settings.groq_api_key:
            return ChatGroq(
                model=settings.groq_model or 'llama-3.3-70b-versatile',
                temperature=0,
                groq_api_key=settings.groq_api_key,
            )
        return ChatOpenAI(model='gpt-4.1-mini', temperature=0, api_key=settings.openai_api_key)

    raise RuntimeError(f'Chat agent does not support MODEL_PROVIDER={provider}')


_agent = None


def get_chat_agent():
    global _agent
    if _agent is None:
        llm = _build_chat_model()
        _agent = create_react_agent(llm, CHAT_TOOLS, prompt=SYSTEM_PROMPT)
    return _agent


def reset_chat_agent():
    """Clear cached agent so tool/prompt updates take effect without restart."""
    global _agent
    _agent = None


def run_chat(message: str, history: List[dict]) -> str:
    agent = get_chat_agent()

    messages = []
    for item in history:
        if item['role'] == 'user':
            messages.append(HumanMessage(content=item['content']))
        elif item['role'] == 'assistant':
            messages.append(AIMessage(content=item['content']))
    messages.append(HumanMessage(content=message))

    result = agent.invoke({'messages': messages}, config={'recursion_limit': 12})
    final_messages = result.get('messages', [])
    if not final_messages:
        return 'I could not generate a response. Please try again.'

    last = final_messages[-1]
    if isinstance(last, AIMessage):
        return last.content or 'Done.'
    return str(last.content) if hasattr(last, 'content') else str(last)
