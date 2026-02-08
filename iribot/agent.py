"""Core Agent logic for handling LLM interactions"""

import json
import logging
from typing import Optional, List, Dict, Any, Generator
from openai import OpenAI
from .config import settings
from .executor import tool_executor

logger = logging.getLogger(__name__)


class Agent:
    """Agent for handling LLM interactions"""

    def __init__(self):
        client_params = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_params["base_url"] = settings.openai_base_url

        self.client = OpenAI(**client_params)
        self.model = settings.openai_model

    def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        images: Optional[List[str]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Send a message to the LLM and stream the response

        Yields:
            Chunks of response data
        """
        # Build messages with system prompt
        formatted_messages = [{"role": "system", "content": system_prompt}]

        # Add image to the last user message if provided
        if images and messages and messages[-1]["role"] == "user":
            last_msg = messages[-1].copy()
            content = [{"type": "text", "text": last_msg.get("content", "")}]

            for image_base64 in images:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    }
                )

            last_msg["content"] = content
            formatted_messages.extend(messages[:-1])
            formatted_messages.append(last_msg)
        else:
            formatted_messages.extend(messages)

        # Get available tools
        tools = tool_executor.get_all_tools()

        log_messages = []
        for message in formatted_messages:
            if message.get("role") == "system":
                log_messages.append({
                    **message,
                    "content": "__system_prompt__",
                })
            else:
                log_messages.append(message)

        logger.info(
            "OpenAI request: %s",
            json.dumps(
                {
                    "model": self.model,
                    "messages": log_messages,
                    "tools": tools,
                    "stream": True,
                },
                ensure_ascii=False,
                default=str,
            ),
        )

        # Call OpenAI API with streaming
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            tools=tools,
            stream=True,
        )

        content = ""
        tool_calls_data = {}  # {index: {id, function: {name, arguments}}}
        finish_reason = None

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None

            if delta:
                # Handle content
                if delta.content:
                    content += delta.content
                    yield {"type": "content", "content": delta.content}

                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {
                                "id": tc.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        if tc.id:
                            tool_calls_data[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_data[idx]["function"][
                                    "name"
                                ] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_data[idx]["function"][
                                    "arguments"
                                ] += tc.function.arguments

            if chunk.choices and chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

        # Yield final result with tool calls
        tool_calls = (
            [tool_calls_data[i] for i in sorted(tool_calls_data.keys())]
            if tool_calls_data
            else []
        )

        yield {
            "type": "done",
            "content": content.strip(),
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
        }

    def process_tool_call(
        self,
        tool_name: str,
        arguments: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a tool call from the LLM

        Args:
            tool_name: Name of the tool to call
            arguments: JSON string of tool arguments

        Returns:
            Result of tool execution
        """
        try:
            args = json.loads(arguments) if arguments else {}
            if tool_name.startswith("shell_") and context:
                if "session_id" not in args and context.get("session_id"):
                    args["session_id"] = context["session_id"]
            result = tool_executor.execute_tool(tool_name, **args)
            return {"success": True, "result": result}
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": f"Invalid JSON arguments: {arguments}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global agent instance
agent = Agent()
