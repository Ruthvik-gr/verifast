import os
import aiohttp
import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqService:
    """Service for generating responses using Groq API"""
    
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"  # Default model
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            
    async def generate_response(self, query: str, context: str, chat_history: List[Dict[str, Any]] = None) -> str:
        """Generate a complete response using Groq API"""
        if not self.api_key:
            return "Error: Groq API key not configured. Please set the GROQ_API_KEY environment variable."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format the system and user messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful news assistant that provides accurate information based on the provided context. Only answer from the context provided, and if you don't know or can't find the answer in the context, say so."
                }
            ]
            
            # Add chat history for context if available
            if chat_history:
                # Only include the last few messages to avoid token limits
                for msg in chat_history[-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add the current query with context
            messages.append({
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {query}\n\nPlease answer the question based on the context provided."
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from Groq API: {response.status} - {error_text}")
                        return f"Error generating response: {response.status}"
                        
                    response_data = await response.json()
                    answer = response_data["choices"][0]["message"]["content"]
                    
                    logger.info(f"Generated response with {len(answer)} characters")
                    return answer
                    
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
            
    async def generate_streaming_response(self, query: str, context: str, chat_history: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate a streaming response using Groq API"""
        if not self.api_key:
            yield "Error: Groq API key not configured. Please set the GROQ_API_KEY environment variable."
            return
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Format the system and user messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful news assistant that provides accurate information based on the provided context. Only answer from the context provided, and if you don't know or can't find the answer in the context, say so."
                }
            ]
            
            # Add chat history for context if available
            if chat_history:
                # Only include the last few messages to avoid token limits
                for msg in chat_history[-5:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add the current query with context
            messages.append({
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {query}\n\nPlease answer the question based on the context provided."
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from Groq API: {response.status} - {error_text}")
                        yield f"Error generating response: {response.status}"
                        return
                        
                    # Process the streaming response
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        # Skip empty lines and "data: [DONE]"
                        if not line or line == "data: [DONE]":
                            continue
                            
                        # Parse the data
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])  # Remove "data: " prefix
                                
                                # Extract content if available
                                if "choices" in data and data["choices"] and "delta" in data["choices"][0]:
                                    delta = data["choices"][0]["delta"]
                                    
                                    if "content" in delta and delta["content"]:
                                        yield delta["content"]
                                        
                            except Exception as e:
                                logger.error(f"Error parsing streaming response: {e}")
                                yield f"\nError parsing response: {str(e)}"
                                return
                        
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error generating response: {str(e)}"
            

class MockGroqService:
    """Mock service for generating responses without API keys"""
    
    def __init__(self):
        logger.warning("Using MockGroqService - responses will be simulated and not useful for production")
        
    async def generate_response(self, query: str, context: str, chat_history: List[Dict[str, Any]] = None) -> str:
        """Generate a mock response for testing"""
        # Extract some text from the context to simulate a relevant response
        context_preview = context[:200] + "..." if len(context) > 200 else context
        
        response = f"Here's what I found about '{query}':\n\n"
        response += f"Based on the news articles, {context_preview}\n\n"
        response += "Please note this is a simulated response as the Groq API key is not configured."
        
        return response
        
    async def generate_streaming_response(self, query: str, context: str, chat_history: List[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate a mock streaming response for testing"""
        # Create a simulated response using parts of the context
        import asyncio
        
        response_parts = [
            f"Here's what I found about '{query}':\n\n",
            "Based on the news articles, ",
            context[:50] + "..." if len(context) > 50 else context,
            "\n\nPlease note this is a simulated response as the Groq API key is not configured."
        ]
        
        for part in response_parts:
            # Split the part into smaller chunks to simulate streaming
            words = part.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3])
                yield chunk + " "
                await asyncio.sleep(0.1)
                

def get_groq_service():
    """Factory function to get the appropriate Groq service"""
    # If GROQ_API_KEY is available, use the real service
    if os.environ.get("GROQ_API_KEY"):
        return GroqService()
    else:
        # Otherwise use the mock service for testing
        return MockGroqService()
