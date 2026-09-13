# ==========================================================================
# JARVIS Google Gemini Provider Adapter
# ==========================================================================

import time
from typing import List, Dict, Any, Optional
import httpx

from server.ai.providers.base import LLMClient, AIResponse, ToolCallPlan, ProviderTestResult
from server.ai.prompts import JARVIS_SYSTEM_PROMPT

class GeminiProvider(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        display_name: str = "Google Gemini",
        temperature: float = 0.4,
        max_output_tokens: int = 1024,
        timeout_seconds: float = 25.0
    ):
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.display_name = display_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.timeout_seconds = timeout_seconds

    def _get_url(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    async def test_connection(self) -> ProviderTestResult:
        url = self._get_url()
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 5}
        }
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                latency_ms = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    return ProviderTestResult(
                        status="CONNECTED",
                        message=f"Gemini LLM connected successfully. Model: {self.model}",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )

                if resp.status_code in (400, 401, 403):
                    return ProviderTestResult(
                        status="INVALID_KEY",
                        message="Google Gemini API key was rejected. Verify your Gemini API credentials.",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )
                elif resp.status_code == 404:
                    return ProviderTestResult(
                        status="MODEL_NOT_FOUND",
                        message=f"Gemini model '{self.model}' not found.",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )
                elif resp.status_code == 429:
                    return ProviderTestResult(
                        status="RATE_LIMITED",
                        message="Gemini API rate limit or quota exceeded.",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )
                else:
                    return ProviderTestResult(
                        status="PROVIDER_ERROR",
                        message=f"Gemini returned error status {resp.status_code}.",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderTestResult(
                status="TIMEOUT",
                message=f"Gemini API request timed out after {self.timeout_seconds}s.",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            clean_err = str(e).replace(self.api_key, "[REDACTED]")
            return ProviderTestResult(
                status="PROVIDER_UNREACHABLE",
                message=f"Could not connect to Gemini API: {clean_err[:100]}",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload: Dict[str, Any] = {
            "system_instruction": {
                "parts": [{"text": JARVIS_SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens
            }
        }

        if tools:
            func_declarations = []
            for t in tools:
                func_declarations.append({
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters_schema", {})
                })
            payload["tools"] = [{"function_declarations": func_declarations}]

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(self._get_url(), json=payload)
                if resp.status_code != 200:
                    return AIResponse(
                        content=f"[GEMINI ERROR] HTTP {resp.status_code} returned by Gemini API.",
                        model=self.model
                    )

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return AIResponse(content="No response generated by Gemini.", model=self.model)

                first_part = candidates[0].get("content", {}).get("parts", [{}])[0]
                if "functionCall" in first_part:
                    fc = first_part["functionCall"]
                    return AIResponse(
                        tool_call=ToolCallPlan(
                            tool_name=fc.get("name", ""),
                            parameters=fc.get("args", {}),
                            rationale="Gemini function call planned"
                        ),
                        model=self.model
                    )

                text_content = first_part.get("text", "")
                return AIResponse(content=text_content.strip(), model=self.model)

        except Exception as e:
            clean_err = str(e).replace(self.api_key, "[REDACTED]")
            return AIResponse(
                content=f"[NEURAL LINK ERROR] Gemini provider failure: {clean_err[:100]}",
                model=self.model
            )
