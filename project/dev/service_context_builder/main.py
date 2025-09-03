import asyncio
from typing import Any, Dict, List
from fastmcp import FastMCP
from loguru import logger

# Initialize MCP server
mcp = FastMCP("Context Builder Service")


@mcp.tool()
async def build_context(
    query: str,
    retrieved_docs: List[Dict[str, Any]],
    max_length: int = 4000,
    template: str = "default"
) -> Dict[str, Any]:
    """Build context from retrieved documents."""
    logger.info(f"Building context for query: {query[:100]}...")
    
    context = f"Query: {query}\n\nRetrieved Documents:\n"
    for i, doc in enumerate(retrieved_docs[:5]):  # Limit to top 5
        context += f"{i+1}. {doc.get('content', '')[:500]}...\n\n"
    
    return {
        "context": context[:max_length],
        "doc_count": len(retrieved_docs),
        "template_used": template,
        "length": len(context[:max_length])
    }


@mcp.tool()
async def create_prompt(
    query: str,
    context: str,
    system_prompt: str = None,
    template_type: str = "qa"
) -> Dict[str, Any]:
    """Create structured prompt from query and context."""
    logger.info(f"Creating {template_type} prompt")
    
    if template_type == "qa":
        prompt = f"""Answer the following question based on the provided context.

Context: {context}

Question: {query}

Answer:"""
    else:
        prompt = f"{system_prompt or ''}\n\nContext: {context}\n\nQuery: {query}"
    
    return {
        "prompt": prompt,
        "template_type": template_type,
        "prompt_length": len(prompt)
    }


async def main():
    await mcp.run(transport_type="stdio", port=8007)


if __name__ == "__main__":
    asyncio.run(main())
