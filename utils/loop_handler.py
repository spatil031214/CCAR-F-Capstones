"""Agentic loop utilities for handling API responses and tool calls."""

import logging
from typing import Callable, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


def format_stop_reason(stop_reason: str) -> str:
    """Format stop_reason for logging."""
    reason_map = {
        "end_turn": "✓ Agent completed turn",
        "tool_use": "→ Tool call requested",
        "max_tokens": "⚠ Reached max tokens",
        "stop_sequence": "⚠ Stop sequence hit",
        "refusal": "✗ Request refused",
    }
    return reason_map.get(stop_reason, f"? Unknown: {stop_reason}")


def handle_tool_use(
    response: Any,
    tools: List[dict],
    tool_executor: Optional[Callable[[str, dict], str]] = None,
) -> List[dict]:
    """
    Extract and handle tool calls from API response.

    Args:
        response: The API response potentially containing tool calls
        tools: List of available tool definitions
        tool_executor: Optional callable that executes a tool (name, input_dict) -> str result

    Returns:
        List of tool result blocks to append to messages
    """
    tool_results = []

    # OpenAI format: Check if response has tool calls
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            logger.debug(f"Executing tool: {tool_call.function.name}")

            if tool_executor:
                try:
                    result = tool_executor(tool_call.function.name, tool_call.function.arguments)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result,
                    })
                    logger.debug(f"Tool {tool_call.function.name} executed successfully")
                except Exception as e:
                    logger.error(f"Tool execution failed: {str(e)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": f"Error: {str(e)}",
                    })

    return tool_results


class AgenticLoop:
    """Manages the agentic loop with proper response handling."""

    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4-turbo",
        max_iterations: int = 10,
        debug: bool = False,
    ):
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.debug = debug

    async def run(
        self,
        messages: List[dict],
        system: str,
        tools: Optional[List[dict]] = None,
        tool_executor: Optional[Callable[[str, dict], str]] = None,
    ) -> Any:
        """
        Run the agentic loop until completion.

        Args:
            messages: Initial messages
            system: System prompt
            tools: Optional available tools
            tool_executor: Optional function to execute tools

        Returns:
            Final response from the API
        """
        iteration = 0
        current_messages = messages.copy()

        while iteration < self.max_iterations:
            iteration += 1

            if self.debug:
                logger.debug(f"Loop iteration {iteration}/{self.max_iterations}")

            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                messages=current_messages,
            )

            logger.debug(f"Response finish_reason: {response.choices[0].finish_reason}")

            # Check finish reason
            if response.choices[0].finish_reason == "stop":
                logger.debug("Agent completed")
                return response

            elif response.choices[0].finish_reason == "tool_calls":
                # Handle tool calls if needed
                tool_results = handle_tool_use(response.choices[0].message, tools, tool_executor)
                if tool_results:
                    current_messages.append({
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    })
                    current_messages.append({
                        "role": "user",
                        "content": tool_results,
                    })
                else:
                    return response
            else:
                logger.warning(f"Finish reason: {response.choices[0].finish_reason}")
                return response

        logger.error(f"Hit max iterations ({self.max_iterations})")
        return response
