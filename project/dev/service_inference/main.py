import asyncio
from typing import Any, Dict, List, Union, Optional
from fastmcp import FastMCP
from loguru import logger

from .config import settings
from .handlers import InferenceHandler


# Initialize MCP server
mcp = FastMCP("Inference Service")

# Initialize handlers
inference_handler = InferenceHandler()


@mcp.tool()
async def generate_text(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_prompt: str = None,
    context: List[str] = None
) -> Dict[str, Any]:
    """
    Generate text using specified language model.
    
    Args:
        prompt: Input prompt for generation
        model: Model to use for generation
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        system_prompt: System prompt for model
        context: Additional context for generation
    
    Returns:
        Dictionary with generated text and metadata
    """
    try:
        response = await inference_handler.generate_text(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            context=context or []
        )
        
        return response
    except Exception as e:
        logger.error(f"Error in generate_text tool: {e}")
        raise


@mcp.tool()
async def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = False
) -> Dict[str, Any]:
    """
    Generate chat completion response.
    
    Args:
        messages: List of chat messages
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        stream: Whether to stream response
    
    Returns:
        Dictionary with chat response
    """
    try:
        response = await inference_handler.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        return response
    except Exception as e:
        logger.error(f"Error in chat_completion tool: {e}")
        raise


@mcp.tool()
async def analyze_sentiment(
    text: str,
    model: str = "default"
) -> Dict[str, Any]:
    """
    Analyze sentiment of text.
    
    Args:
        text: Text to analyze
        model: Model to use for sentiment analysis
    
    Returns:
        Dictionary with sentiment analysis results
    """
    try:
        result = await inference_handler.analyze_sentiment(text, model)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_sentiment tool: {e}")
        raise


@mcp.resource()
async def get_available_models() -> str:
    """Get list of available inference models."""
    models = {
        "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        "anthropic": ["claude-3-sonnet", "claude-3-haiku"],
        "local": ["llama2", "mistral", "codellama"],
        "huggingface": ["bert-base-uncased", "distilbert-base-uncased"]
    }
    return f"Available models: {models}"


async def main():
    """Run the MCP server"""
    logger.add(
        "logs/inference_service.log",
        rotation="1 day",
        retention="30 days",
        format=settings.log_format,
        level=settings.log_level
    )
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    try:
        await mcp.run(
            transport_type="stdio",
            host=settings.mcp_server_host,
            port=settings.mcp_server_port
        )
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
