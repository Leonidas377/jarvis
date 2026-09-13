# ==========================================================================
# JARVIS Universal OpenAI-Compatible Provider Adapter
# Connects to NVIDIA NIM, OpenAI, Groq, DeepSeek, Together, OpenRouter, vLLM
# Enforces strict SSRF validation, secret redaction, and normalized diagnostics
# ==========================================================================

import time
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import httpx

from server.ai.providers.base import LLMClient, AIResponse, ToolCallPlan, ProviderTestResult
from server.services.extraction.security import validate_url_safe, SecurityException
from server.ai.prompts import JARVIS_SYSTEM_PROMPT

class OpenAICompatibleProvider(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        display_name: str = "OpenAI-Compatible",
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        timeout_seconds: float = 30.0
    ):
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.display_name = display_name
        self.organization_id = organization_id.strip() if organization_id else None
        self.project_id = project_id.strip() if project_id else None
        self.temperature = max(0.0, min(1.5, temperature))
        self.max_output_tokens = max(16, min(4096, max_output_tokens))
        self.timeout_seconds = timeout_seconds

        # SSRF Validation on Base URL
        self._validate_base_url()

    def _validate_base_url(self):
        """Validates that base_url does not point to restricted private/internal endpoints."""
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP/HTTPS are supported.")
        if not parsed.hostname:
            raise ValueError("Base URL must include a valid hostname.")

        # Local development allowlist
        lower_host = parsed.hostname.lower()
        if lower_host in {"localhost", "127.0.0.1", "::1"}:
            # Allowed for local model runtimes like Ollama / vLLM if explicitly configured
            return

        # Enforce public safety check
        try:
            validate_url_safe(self.base_url)
        except SecurityException as e:
            raise ValueError(f"Base URL violates security policy: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "JARVIS-Core-Agent/2.0"
        }
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id
        if self.project_id:
            headers["OpenAI-Project"] = self.project_id
        return headers

    async def test_connection(self) -> ProviderTestResult:
        """
        Executes a minimal non-sensitive connectivity check.
        Never sends user conversation history or leaks raw secrets.
        """
        endpoint = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "temperature": 0.0
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                latency_ms = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    return ProviderTestResult(
                        status="CONNECTED",
                        message=f"JARVIS LLM connected successfully. Provider: {self.display_name} | Model: {self.model}",
                        provider=self.display_name,
                        model=self.model,
                        latency_ms=latency_ms
                    )

                # Error categorization
                return self._normalize_error(resp.status_code, resp.text, latency_ms)

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderTestResult(
                status="TIMEOUT",
                message=f"Connection timed out after {self.timeout_seconds}s while contacting {self.display_name}.",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderTestResult(
                status="PROVIDER_UNREACHABLE",
                message=f"Could not connect to {self.display_name}: {self._sanitize_error_msg(str(e))}",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIResponse:
        """Generates conversational response or structured tool planning."""
        endpoint = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        # Format system prompt + messages
        formatted_messages = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]
        for m in messages:
            role = m.get("role", "user")
            if role in ["system", "user", "assistant"]:
                formatted_messages.append({"role": role, "content": m.get("content", "")})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens
        }

        # Format tool definitions if provided
        if tools:
            openai_tools = []
            for t in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters_schema", {"type": "object", "properties": {}})
                    }
                })
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                if resp.status_code != 200:
                    norm = self._normalize_error(resp.status_code, resp.text, 0)
                    return AIResponse(
                        content=f"[NEURAL LINK ERROR] {norm.message}",
                        model=self.model
                    )

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return AIResponse(content="No response generated by provider.", model=self.model)

                choice_msg = choices[0].get("message", {})

                # Check for tool call
                tool_calls = choice_msg.get("tool_calls", [])
                if tool_calls:
                    first_tool = tool_calls[0]
                    func = first_tool.get("function", {})
                    tool_name = func.get("name", "")
                    raw_args = func.get("arguments", "{}")
                    parsed_params = {}
                    if isinstance(raw_args, str):
                        try:
                            parsed_params = json.loads(raw_args)
                        except Exception:
                            parsed_params = {}
                    elif isinstance(raw_args, dict):
                        parsed_params = raw_args

                    return AIResponse(
                        tool_call=ToolCallPlan(
                            tool_name=tool_name,
                            parameters=parsed_params,
                            rationale=f"Model selected tool {tool_name}"
                        ),
                        model=self.model
                    )

                # Standard text response
                content = choice_msg.get("content", "") or ""
                return AIResponse(content=content.strip(), model=self.model)

        except httpx.TimeoutException:
            return AIResponse(
                content=f"[PROVIDER TIMEOUT] The requested LLM at {self.display_name} took longer than {self.timeout_seconds}s to respond.",
                model=self.model
            )
        except Exception as e:
            return AIResponse(
                content=f"[PROVIDER ERROR] Failed to connect to {self.display_name}: {self._sanitize_error_msg(str(e))}",
                model=self.model
            )

    def _normalize_error(self, status_code: int, response_text: str, latency_ms: int) -> ProviderTestResult:
        """Categorizes HTTP status codes into safe, normalized diagnostics."""
        clean_text = self._sanitize_error_msg(response_text)

        if status_code in (401, 403):
            return ProviderTestResult(
                status="INVALID_KEY",
                message="The API key was rejected by the provider. Please verify your credentials.",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        elif status_code in (404, 410):
            return ProviderTestResult(
                status="MODEL_NOT_FOUND",
                message=f"The model '{self.model}' was not found or is retired/inactive for your account.",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        elif status_code == 429:
            return ProviderTestResult(
                status="RATE_LIMITED",
                message="Provider quota or rate limit exceeded. Please check your provider account credits.",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        elif 500 <= status_code < 600:
            return ProviderTestResult(
                status="PROVIDER_ERROR",
                message=f"The remote provider encountered an internal server error (HTTP {status_code}).",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )
        else:
            return ProviderTestResult(
                status="CONFIGURATION_ERROR",
                message=f"Provider returned error HTTP {status_code}: {clean_text[:120]}",
                provider=self.display_name,
                model=self.model,
                latency_ms=latency_ms
            )

    def _sanitize_error_msg(self, msg: str) -> str:
        """Ensures secrets and auth tokens never leak in error messages."""
        if not msg:
            return "Unknown error"
        sanitized = msg.replace(self.api_key, "[REDACTED_API_KEY]")
        if len(self.api_key) > 8:
            sanitized = sanitized.replace(self.api_key[-8:], "[REDACTED]")
        return sanitized[:200]
