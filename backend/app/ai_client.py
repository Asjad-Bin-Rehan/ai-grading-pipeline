import json
from typing import Any, Dict
import httpx

from .config import settings

class LLMClient:
    def __init__(self, provider: str):
        self.provider = provider.lower()
        self._client = httpx.Client(timeout=60)

    def grade(self, prompt: str) -> str:
        if self.provider == 'openai':
            return self._call_openai(prompt)
        if self.provider == 'anthropic':
            return self._call_anthropic(prompt)
        if self.provider == 'groq':
            return self._call_groq(prompt)
        if self.provider in ('local', 'mock', 'demo'):
            return self._call_mock(prompt)
        raise ValueError('Unsupported model provider: ' + self.provider)

    def _call_openai(self, prompt: str) -> str:
        if not settings.openai_api_key:
            raise RuntimeError('OPENAI_API_KEY is not configured')
        payload = {
            'model': 'gpt-4.1-mini',
            'temperature': 0,
            'messages': [
                {'role': 'system', 'content': 'You are a deterministic grading assistant.'},
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': 1800,
        }
        headers = {
            'Authorization': f'Bearer {settings.openai_api_key}',
            'Content-Type': 'application/json',
        }
        response = self._client.post('https://api.openai.com/v1/chat/completions', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    def _call_anthropic(self, prompt: str) -> str:
        if not settings.anthropic_api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not configured')
        payload = {
            'model': 'claude-3.0',
            'temperature': 0,
            'max_tokens_to_sample': 1800,
            'prompt': prompt,
        }
        headers = {
            'x-api-key': settings.anthropic_api_key,
            'Content-Type': 'application/json',
        }
        response = self._client.post('https://api.anthropic.com/v1/complete', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['completion']

    def _call_groq(self, prompt: str) -> str:
        if not settings.groq_api_key:
            raise RuntimeError('GROQ_API_KEY is not configured')
        # Allow model and base URL to be configured via environment variables.
        model = settings.groq_model or 'llama-3.1-70b-versatile'
        base_url = (settings.groq_base_url or 'https://api.groq.com').rstrip('/')

        payload = {
            'model': model,
            'temperature': 0,
            'messages': [
                {'role': 'system', 'content': 'You are a deterministic grading assistant for academic quizzes.'},
                {'role': 'user', 'content': prompt},
            ],
            'max_tokens': 2000,
        }

        headers = {
            'Authorization': f'Bearer {settings.groq_api_key}',
            'Content-Type': 'application/json',
        }

        # Use the OpenAI-compatible path which Groq supports for many accounts.
        url = f"{base_url}/openai/v1/chat/completions"
        response = self._client.post(url, json=payload, headers=headers)

        # If the request failed, include the response text in the exception for easier debugging.
        if response.status_code != 200:
            try:
                err_text = response.text
            except Exception:
                err_text = '<unreadable response body>'
            raise RuntimeError(f'Groq API request failed: {response.status_code} - {err_text}')

        return response.json()['choices'][0]['message']['content']

    def _call_mock(self, prompt: str) -> str:
        """Mock grader for demo/testing without API keys."""
        # Extract student ID from prompt if possible
        student_id = "student_mock"
        if "student" in prompt.lower():
            lines = prompt.split("\n")
            for line in lines:
                if "student_id" in line.lower():
                    parts = line.split(":")
                    if len(parts) > 1:
                        student_id = parts[-1].strip()
                    break
        
        # Return a realistic mock grading response matching expected schema
        return json.dumps({
            "student_id": student_id,
            "overall_score": 72.0,
            "question_evaluations": [
                {
                    "question_number": 1,
                    "step_by_step_analysis": "Student correctly distinguished capital expenditure from revenue expenditure and provided valid examples. Minor deduction for incomplete explanation of long-term benefit aspect.",
                    "points_awarded": 8.5
                },
                {
                    "question_number": 2,
                    "step_by_step_analysis": "Good coverage of GST input tax credit steps. Student mentioned tax invoice requirement and eligibility check. However, missing details on return filing procedures and record maintenance requirements.",
                    "points_awarded": 6.0
                },
                {
                    "question_number": 3,
                    "step_by_step_analysis": "Calculation is correct: 120,000 x 10% = 12,000. Student showed the formula properly. Deduction for not clearly stating this is first-year depreciation and not explaining the straight-line method in detail.",
                    "points_awarded": 5.5
                }
            ],
            "needs_human_review": False
        })


def get_llm_client() -> LLMClient:
    return LLMClient(settings.model_provider)


def parse_json_response(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if not raw.startswith('{'):
        json_start = raw.find('{')
        raw = raw[json_start:] if json_start >= 0 else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError('LLM response could not be parsed as JSON') from exc
