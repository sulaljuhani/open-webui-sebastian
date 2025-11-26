"""
OpenWebUI Pipe Function for Sebastian AI Stack - Streaming Edition

This Pipe provides real-time streaming integration with the custom LangGraph
multi-agent backend system using Server-Sent Events (SSE).

Features:
- Real-time token-by-token streaming responses
- Full conversation continuity via chat_id
- Single-user system (hardcoded user ID)
- OpenAI-compatible streaming interface

Installation:
1. Copy this file content
2. In Open WebUI, go to Workspace > Functions
3. Click "+" to create a new function
4. Paste this code
5. Set the valves (especially BACKEND_URL)
6. Save and enable the function

Usage:
- The function will appear as "Sebastian" in the model dropdown
- Select it and chat normally
- Responses stream in real-time word-by-word
"""

import json
import requests
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        """Configuration parameters for the Sebastian integration."""

        BACKEND_URL: str = Field(
            default="http://host.docker.internal:8000",
            description="Backend API URL (use host.docker.internal for Docker, or direct IP)"
        )
        API_KEY: str = Field(
            default="",
            description="Optional API key for backend authentication (X-API-Key header)"
        )
        USER_ID: str = Field(
            default="00000000-0000-0000-0000-000000000001",
            description="Single-user ID (DO NOT CHANGE - all data stored under this ID)"
        )
        MODEL_NAME: str = Field(
            default="sebastian",
            description="Model identifier to send to backend"
        )
        REQUEST_TIMEOUT: int = Field(
            default=120,
            description="Request timeout in seconds"
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="Enable debug logging"
        )
        SHOW_AGENT_NAME: bool = Field(
            default=False,
            description="Show which agent handled the request (future feature)"
        )

    def __init__(self):
        self.type = "manifold"
        self.id = "sebastian"
        self.name = "Sebastian: "
        self.valves = self.Valves()

    def pipes(self) -> List[dict]:
        """Return available models as selectable options."""
        return [
            {
                "id": "sebastian",
                "name": "Sebastian"
            }
        ]

    def pipe(
        self,
        body: dict,
        __user__: dict = None,
        __metadata__: dict = None,
        __event_emitter__=None,
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipe function that streams chat responses from the backend.

        Args:
            body: Chat request body with messages, model, etc.
            __user__: OpenWebUI user information (NOT USED - single-user system)
            __metadata__: Rich metadata including chat_id
            __event_emitter__: Event emitter for status updates

        Yields:
            Streamed response chunks from the backend
        """
        if self.valves.DEBUG_MODE:
            print(f"[Sebastian Pipe] Starting request")

        # Extract messages from body
        messages = body.get("messages", [])
        if not messages:
            return "Error: No messages provided"

        # Get chat_id for conversation continuity
        chat_id = __metadata__.get("chat_id") if __metadata__ else None

        # Build request payload (OpenAI-compatible)
        # Convert OpenWebUI messages to backend format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        selected_model = body.get("model") or self.valves.MODEL_NAME

        payload = {
            "model": selected_model,
            "messages": formatted_messages,
            "stream": True,
            "user": self.valves.USER_ID
        }

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        if self.valves.API_KEY:
            headers["X-API-Key"] = self.valves.API_KEY

        # Construct endpoint URL
        endpoint = f"{self.valves.BACKEND_URL}/v1/chat/completions"

        if self.valves.DEBUG_MODE:
            print(f"[Sebastian Pipe] Endpoint: {endpoint}")
            print(f"[Sebastian Pipe] Chat ID: {chat_id}")
            print(f"[Sebastian Pipe] Messages: {len(formatted_messages)}")

        # Emit status if available
        if __event_emitter__:
            __event_emitter__({
                "type": "status",
                "data": {"description": "Connecting to Sebastian...", "done": False}
            })

        try:
            # Make streaming request
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.valves.REQUEST_TIMEOUT,
                stream=True  # Enable streaming
            )

            if response.status_code >= 400:
                error_msg = f"Backend error ({response.status_code}): {response.text}"
                print(f"[Sebastian Pipe] ERROR: {error_msg}")

                if __event_emitter__:
                    __event_emitter__({
                        "type": "status",
                        "data": {"description": "Error from backend", "done": True}
                    })

                return f"Error: {error_msg}"

            # Clear initial status
            if __event_emitter__:
                __event_emitter__({
                    "type": "status",
                    "data": {"description": "Receiving response...", "done": True}
                })

            # Stream the response
            full_response = ""
            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode('utf-8')

                # Skip empty lines and comments
                if not line_str.strip() or line_str.startswith(':'):
                    continue

                # Check for completion signal
                if line_str.strip() == "data: [DONE]":
                    if self.valves.DEBUG_MODE:
                        print(f"[Sebastian Pipe] Stream completed")
                    break

                # Parse SSE event
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix

                    try:
                        data = json.loads(data_str)

                        # Check for error
                        if "error" in data:
                            error_msg = data["error"].get("message", "Unknown error")
                            print(f"[Sebastian Pipe] Stream error: {error_msg}")
                            yield f"\n\nError: {error_msg}"
                            break

                        # Extract content from OpenAI-compatible format
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                full_response += content
                                yield content

                    except json.JSONDecodeError as e:
                        if self.valves.DEBUG_MODE:
                            print(f"[Sebastian Pipe] JSON decode error: {e}")
                        continue

            if self.valves.DEBUG_MODE:
                print(f"[Sebastian Pipe] Total response length: {len(full_response)}")

            # If no response was streamed, return error
            if not full_response:
                return "Error: No response received from backend"

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.valves.REQUEST_TIMEOUT}s"
            print(f"[Sebastian Pipe] ERROR: {error_msg}")

            if __event_emitter__:
                __event_emitter__({
                    "type": "status",
                    "data": {"description": "Request timeout", "done": True}
                })

            return f"Error: {error_msg}"

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            print(f"[Sebastian Pipe] ERROR: {error_msg}")

            if __event_emitter__:
                __event_emitter__({
                    "type": "status",
                    "data": {"description": "Connection failed", "done": True}
                })

            return f"Error: Could not connect to backend. Check BACKEND_URL in valves."

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[Sebastian Pipe] ERROR: {error_msg}")

            if __event_emitter__:
                __event_emitter__({
                    "type": "status",
                    "data": {"description": "Unexpected error", "done": True}
                })

            return f"Error: {error_msg}"
