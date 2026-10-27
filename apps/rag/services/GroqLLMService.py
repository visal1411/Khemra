import json
import logging
from typing import Any, Dict, List
import requests
from django.conf import settings

from apps.rag.services.BaseLLMService import BaseLLMService

logger = logging.getLogger(__name__)


class GroqLLMService(BaseLLMService):
    """
    Groq LLM provider implementation using OpenAI-compatible REST completions.
    Synthesizes search results into a concise summary and sequential steps
    grounded strictly in the retrieved knowledge segments.
    """

    SYSTEM_PROMPT = """You are an expert procedural AI assistant designed to synthesize search results into clear, step-by-step instructions.

You will be given a user's question and a list of verified knowledge segments retrieved from company videos and documents.

Your job:
1. Provide a concise, beginner-friendly 'summary' directly answering the user's question in a clear, natural tone.
2. Break down the process into granular, sequential 'steps' (1, 2, 3...). If the context contains multiple distinct actions, tasks, or recommendations (even within a single stage or phase), break them down into separate actionable steps.
3. For each step:
   - Provide an action-oriented 'title' (e.g. "Brainstorm and Gather Business Ideas").
   - Provide a clear, detailed 'instruction' thoroughly explaining what to do based on all facts in the text.
   - Attach the exact 'segment_id' of the source segment that explains or demonstrates this step.

CRITICAL RULES & CONSTRAINTS:
- Minimum Steps: ALWAYS provide at least 2 to 5 distinct sequential steps in the 'steps' array whenever the source material contains multiple actions, tasks, or recommendations. NEVER return only 1 single step. Even if the user asks for 'the first step' or a single topic, break down that process into its granular sequential sub-actions (e.g. Step 1: Brainstorm ideas, Step 2: Evaluate pros/cons & market potential, Step 3: Consult trusted advisors).
- Language: ALWAYS output the entire response strictly in English. Even if the user's question is in Khmer, the target language parameter is "km", or the provided source materials contain Khmer text, all fields ('summary', 'title', 'instruction') MUST be written in clear English. Never output in Khmer.
- Beginner-Friendly & Accessible: Ensure the content is easy to understand for users who have little or no prior knowledge of business management. Use simple, accessible English, avoid complex business jargon, and explain concepts straightforwardly so anyone can easily follow.
- Strict Factual Grounding (Anti-Hallucination): You must answer STRICTLY and ONLY based on the facts explicitly stated in the provided segment 'summary' and 'transcript'.
- Zero Outside Information: Do NOT invent, extrapolate, speculate, or make assumptions. Do NOT mention external tools, websites, buttons, or procedures that are not explicitly present in the provided text.
- Missing Information: If the provided segments do not fully answer the question or lack certain procedural details, state ONLY what is documented and do NOT fill in the blanks with outside knowledge.
- Referential Integrity: 'segment_id' MUST exactly match one of the segment UUIDs provided in the context.
- Format: You must output ONLY a valid JSON object matching this schema:
  {
    "summary": "Cohesive natural language answer summary in English...",
    "steps": [
      {
        "step_number": 1,
        "title": "Short title in English",
        "instruction": "Detailed instruction in English...",
        "segment_id": "exact-uuid-from-context"
      }
    ]
  }"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        api_base: str = None,
        timeout: float = 8.0,
    ):
        self.api_key = api_key or getattr(settings, "GROQ_API_KEY", "")
        self.model = model or getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b")
        raw_base = api_base or getattr(settings, "GROQ_API_BASE", "https://api.groq.com/openai/v1")
        self.api_base = raw_base.rstrip("/")
        self.timeout = getattr(settings, "GROQ_TIMEOUT", timeout)

    def _format_context(self, segments: List[Dict[str, Any]]) -> str:
        blocks = []
        for s in segments:
            seg_id = str(s.get("segment_id", ""))
            doc_title = s.get("knowledge_title") or ""
            seg_title = s.get("title") or ""
            summary = s.get("summary") or ""
            transcript = s.get("transcript") or ""

            block = (
                f"[Segment ID: {seg_id}]\n"
                f"Document: {doc_title}\n"
                f"Title: {seg_title}\n"
                f"Summary: {summary}\n"
                f"Transcript: {transcript}"
            )
            blocks.append(block)
        return "\n---\n".join(blocks)

    def generate_ai_overview(
        self,
        question: str,
        language: str,
        segments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize search results into a revised summary and grounded steps.
        Falls back to summary=None and steps=[] upon any error or missing API key.
        """
        fallback_response = {"summary": None, "steps": []}

        if not segments:
            return fallback_response

        if not self.api_key:
            logger.warning("GROQ_API_KEY is not configured. Falling back to default search.")
            return fallback_response

        context_str = self._format_context(segments)
        user_message = (
            f"User Question: {question}\n"
            f"Output Language: English (MANDATORY: Output all summary, titles, and instructions strictly in English, even if the requested language is '{language}')\n\n"
            f"Verified Knowledge Segments:\n---\n{context_str}\n---\n"
            f"CRITICAL REMINDER: Synthesize your answer and steps using ONLY the facts explicitly provided in the summary and transcript above. "
            f"Break down the answer into at least 2 to 5 distinct, sequential sub-steps (NEVER return only 1 step). "
            f"Do NOT invent any steps, external URLs, tools, or procedures. "
            f"Write the entire response strictly in English."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "top_p": 0.9,
            "response_format": {"type": "json_object"},
        }

        endpoint = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                logger.error(
                    f"Groq API returned error status {response.status_code}: {response.text}"
                )
                return fallback_response

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            summary = parsed.get("summary")
            steps = parsed.get("steps") if isinstance(parsed.get("steps"), list) else []

            return {
                "summary": summary if isinstance(summary, str) else None,
                "steps": steps,
            }
        except requests.exceptions.Timeout:
            logger.warning(f"Groq API call timed out after {self.timeout}s.")
            return fallback_response
        except Exception as e:
            logger.error(f"Failed to generate AI overview via Groq: {e}")
            return fallback_response
