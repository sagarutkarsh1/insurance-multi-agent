from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService
from vector_store import vector_store
import json
from typing import AsyncGenerator, Dict
import os
import logging
import traceback
from google.genai import types  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"

# Validate API keys on module load
if not os.getenv("GOOGLE_API_KEY"):
    logger.error("GOOGLE_API_KEY environment variable not set!")
    raise ValueError("GOOGLE_API_KEY is required")

if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY environment variable not set!")
    raise ValueError("OPENAI_API_KEY is required")

logger.info(f"Agent module initialized with model: {MODEL}")

def search_internal_docs(query: str, num_results: int = 5) -> str:
    """
    Search internal insurance policy documents for relevant information.
    
    Args:
        query: The search query to find relevant policy information
        num_results: Number of results to return (default 5)
    
    Returns:
        JSON string containing relevant document chunks and metadata
    """
    try:
        logger.info(f"search_internal_docs called with query: {query}")
        results = vector_store.search(query, n_results=num_results)
        logger.info(f"Retrieved {len(results)} results from vector store")
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error in search_internal_docs: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e), "results": []})

def create_rag_agent() -> LlmAgent:
    """RAG agent that searches internal documents"""
    return LlmAgent(
        name="RAGAgent",
        model=MODEL,
        instruction="""You are a RAG specialist agent for insurance compliance.

Your job: Search internal insurance policy documents to find relevant evidence.

When to use:
- Check internal coverage limits
- Verify underwriting guidelines  
- Find policy exclusions
- Review claim procedures

How to work:
1. Use search_internal_docs() to search embedded documents
2. Analyze retrieved chunks for relevant policy information
3. Cite document sources
4. If you need more evidence, search again with different keywords""",
        tools=[search_internal_docs],
        description="Searches internal insurance policy documents for compliance evidence",
        output_key="internal_evidence"
    )

def create_web_search_agent() -> LlmAgent:
    """Web search agent that searches external sources"""
    return LlmAgent(
        name="WebSearchAgent",
        model=MODEL,
        instruction="""You are a web search specialist agent for insurance compliance.

Your job: Search the web for external standards, regulations, and industry practices.

When to use:
- Verify against regulatory requirements
- Check industry best practices
- Find legal compliance standards
- Research state/federal insurance laws

How to work:
1. Use google_search() to find relevant external information
2. Focus on authoritative sources (gov sites, regulatory bodies, industry standards)
3. Verify information across multiple sources
4. If you need more evidence, search with refined queries""",
        tools=[google_search],
        description="Searches web for external compliance standards and regulations",
        output_key="external_evidence"
    )

def create_analyzer_agent() -> LlmAgent:
    """Final analyzer that synthesizes all evidence"""
    return LlmAgent(
        name="AnalyzerAgent",
        model=MODEL,
        instruction="""You are the final compliance analyzer.

Your job: Synthesize all evidence and produce a structured compliance report.

You will receive:
Findings from internal policy documents
Findings from web search

Your task:
1. Review all evidence collected by previous agents
2. Determine compliance status based on:
   - Internal policy alignment
   - External regulatory compliance
   - Industry best practices
3. Identify any gaps or concerns
4. Provide actionable recommendations

Output Format:
    Compliance Status: COMPLIANT | NON_COMPLIANT | NEEDS_REVIEW
    Confidence: HIGH | MEDIUM | LOW

    Summary:
    Brief, clear explanation of whether the request complies and why.

    Internal Sources Findings:
    Finding 1 written in simple language
    Finding 2 explaining which policy sections apply

    Web Search Findings:
    Finding 1 based on industry or global standards
    Finding 2 comparing with how others handle similar cases

    Gaps:
    Gap or uncertainty in coverage
    Missing documents, exclusions, or risks

    Recommendations:
    Clear action to improve compliance
    Coverage changes or next steps
  """,
        description="Analyzes all evidence and generates final compliance report",
        output_key="final_report"
    )

def create_compliance_workflow() -> SequentialAgent:
    """
    Creates a sequential workflow that:
    1. Searches internal docs (RAG)
    2. Searches web (external standards)
    3. Analyzes and synthesizes final report
    """
    rag_agent = create_rag_agent()
    web_agent = create_web_search_agent()
    analyzer_agent = create_analyzer_agent()
    
    workflow = SequentialAgent(
        name="ComplianceWorkflow",
        sub_agents=[rag_agent, web_agent, analyzer_agent],
        description="Sequential compliance analysis workflow"
    )
    
    return workflow

def create_root_agent() -> LlmAgent:
    """
    Root coordinator agent that decides whether to use:
    - Just RAG agent
    - Just Web Search agent  
    - Both (full workflow)
    """
    compliance_workflow = create_compliance_workflow()
    rag_only = create_rag_agent()
    web_only = create_web_search_agent()
    
    root = LlmAgent(
        name="RootAgent",
        model=MODEL,
        instruction="""You are the root compliance coordinator agent.

Your job: Analyze user queries and route to the appropriate specialist agents.

Decision Logic:
1. **Internal-only queries** → Use RAGAgent directly
   - Examples: "What does our policy say about...", "Check our coverage limits"
   
2. **External-only queries** → Use WebSearchAgent directly
   - Examples: "What are state regulations for...", "Industry standards for..."
   
3. **Compliance analysis** → Use ComplianceWorkflow (both RAG + Web)
   - Examples: "Does this comply?", "Check compliance", "Analyze this request"

When delegating:
- Clearly explain which agent(s) will handle the request
- Let the specialist agents do their work
- Do not present any intermediate results to the user
- Present only the final report to the user

Be intelligent about routing - choose the most efficient path.""",
        sub_agents=[compliance_workflow], #, rag_only, web_only
        description="Root coordinator for insurance compliance analysis"
    )
    
    return root

async def run_agent_stream(query: str) -> AsyncGenerator[Dict, None]:
    """
    Run the agent system and stream events showing which agent is active.
    
    Events emitted:
    - agent_start: When an agent begins execution
    - agent_text: Text output from an agent
    - tool_call: When a tool is being called
    - tool_result: Result from a tool
    - agent_complete: When agent finishes
    """
    
    logger.info(f"Starting agent stream for query: {query}")
    
    try:
        root_agent = create_root_agent()
        session_service = InMemorySessionService()
        runner = InMemoryRunner(agent=root_agent, app_name="Insurance_agent") #, session_service=session_service
        
        # session = session_service.create_session(app_name = "Insurance_agent", user_id="user123")
        # logger.info(f"Created session: {session.id}")
        session = await runner.session_service.create_session(  
            app_name="Insurance_agent",   
            user_id="user123"  
        ) 
        logger.info(f"Created session: {session.id}")
        
        current_agent = "RootAgent"
        
        yield {
            "type": "agent_start",
            "agent": current_agent,
            "message": "Analyzing query and routing to specialist agents..."
        }
        
        event_count = 0
        content = types.Content(  
            role="user",   
            parts=[types.Part.from_text(text=query)]  
        )  
        async for event in runner.run_async(
            session_id=session.id,
            new_message=content,
            user_id="user123"
        ):
            event_count += 1
            logger.debug(f"Event {event_count}: {type(event).__name__}")
            
            # Track current agent
            if hasattr(event, 'author') and event.author:
                current_agent = event.author
                logger.info(f"Agent active: {current_agent}")
                
                yield {
                    "type": "agent_active",
                    "agent": current_agent
                }
            
            # Process event content
            if hasattr(event, 'content') and event.content:
                content = event.content
                
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        # Text output
                        if hasattr(part, 'text') and part.text:
                            logger.debug(f"Text from {current_agent}: {part.text[:100]}")
                            if current_agent == "AnalyzerAgent":
                                yield {
                                    "type": "agent_text",
                                    "agent": current_agent,
                                    "content": part.text
                                }
                        
                        # Tool call
                        if part.function_call:
                            func_call = part.function_call
                            tool_name = func_call.name
                            tool_args = dict(func_call.args) if hasattr(func_call, 'args') else {}
                            
                            logger.info(f"Tool call: {tool_name} by {current_agent}")
                            
                            yield {
                                "type": "tool_call",
                                "agent": current_agent,
                                "tool": tool_name,
                                "args": tool_args
                            }
                        
                        # Tool result
                        if part.function_response:
                            func_resp = part.function_response
                            tool_name = func_resp.name if hasattr(func_resp, 'name') else "unknown"
                            
                            logger.info(f"Tool result from: {tool_name}")
                            
                            yield {
                                "type": "tool_result",
                                "agent": current_agent,
                                "tool": tool_name,
                                "result": str(func_resp.response)[:200] if hasattr(func_resp, 'response') else ""
                            }
        
        logger.info(f"Agent execution complete. Total events: {event_count}")
        
        yield {
            "type": "agent_complete",
            "agent": "RootAgent",
            "message": "Compliance analysis complete"
        }
    
    except Exception as e:
        error_msg = f"Error in agent execution: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        yield {
            "type": "error",
            "agent": current_agent if 'current_agent' in locals() else "System",
            "message": error_msg,
            "traceback": traceback.format_exc()
        }