from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from document_processor import doc_processor
from vector_store import vector_store
from agent import run_agent_stream
import json
from typing import List
import logging
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Compliance Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Compliance Analysis System",
        "version": "2.0",
        "framework": "Google ADK"
    }

@app.post("/embed")
async def embed_documents(files: List[UploadFile] = File(...)):
    """
    Upload and embed documents into vector store.
    Accepts PDF and DOCX files.
    """
    try:
        logger.info(f"Received {len(files)} files for embedding")
        
        processed_count = 0
        total_chunks = 0
        errors = []
        
        for file in files:
            try:
                logger.info(f"Processing file: {file.filename}")
                content = await file.read()
                
                chunks = doc_processor.process_document(content, file.filename)
                logger.info(f"Generated {len(chunks)} chunks from {file.filename}")
                
                vector_store.add_documents(chunks)
                
                processed_count += 1
                total_chunks += len(chunks)
                
            except Exception as e:
                error_msg = f"Error processing {file.filename}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        response = {
            "status": "success" if processed_count > 0 else "error",
            "message": f"Successfully embedded {processed_count} documents ({total_chunks} chunks)",
            "files_processed": [f.filename for f in files[:processed_count]],
            "total_chunks": total_chunks
        }
        
        if errors:
            response["errors"] = errors
            response["status"] = "partial_success" if processed_count > 0 else "error"
        
        logger.info(f"Embedding complete: {response}")
        return response
    
    except Exception as e:
        error_msg = f"Fatal error during embedding: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={
            "error": error_msg,
            "traceback": traceback.format_exc()
        })

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """
    Chat with compliance agent (SSE streaming).
    Returns real-time events showing which agent is active.
    """
    logger.info(f"Chat request received: {request.query}")
    
    async def event_generator():
        try:
            event_count = 0
            async for event in run_agent_stream(request.query):
                event_count += 1
                logger.debug(f"Streaming event {event_count}: {event.get('type')}")
                yield f"data: {json.dumps(event)}\n\n"
            
            logger.info(f"Chat stream complete. Total events sent: {event_count}")
            
        except Exception as e:
            error_msg = f"Error in chat stream: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_event = {
                "type": "error",
                "message": error_msg,
                "traceback": traceback.format_exc()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agents": [
            "RootAgent",
            "RAGAgent", 
            "WebSearchAgent",
            "AnalyzerAgent",
            "ComplianceWorkflow"
        ]
    }

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Compliance Analysis System Starting...")
    logger.info("=" * 60)
    logger.info("Checking environment variables...")
    
    import os
    if os.getenv("GOOGLE_API_KEY"):
        logger.info("✓ GOOGLE_API_KEY is set")
    else:
        logger.error("✗ GOOGLE_API_KEY is NOT set!")
    
    if os.getenv("OPENAI_API_KEY"):
        logger.info("✓ OPENAI_API_KEY is set")
    else:
        logger.error("✗ OPENAI_API_KEY is NOT set!")
    
    logger.info("=" * 60)
    logger.info("System ready!")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")