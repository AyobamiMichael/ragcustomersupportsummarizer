# backend/src/services/llm_service.py
"""
LLM service for abstractive summarization using Groq (FREE API)
FIXED: Better error handling and debugging
"""

from typing import List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import json

from ..config import get_settings


class LLMService:
    """
    Service for LLM-based abstractive summarization using Groq API
    
    Groq API is FREE with generous limits:
    - 30 requests per minute
    - Fast inference (tokens/second)
    - Multiple open-source models available
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.api_key = self.settings.GROQ_API_KEY
        
        if self.api_key:
            print(f"✅ LLM Service initialized with Groq API key: {self.api_key[:10]}...")
            self.base_url = "https://api.groq.com/openai/v1"
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        else:
            print("⚠️  WARNING: GROQ_API_KEY not set - abstractive mode will use fallback")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_summary(self, sentences: List[str], 
                              context: Optional[str] = None,
                              style: str = "concise") -> str:
        """
        Generate abstractive summary using Groq API
        
        Args:
            sentences: List of extracted sentences
            context: Optional additional context
            style: Summary style (concise, detailed, bullet)
            
        Returns:
            Generated summary text
        """
        # Check if API is configured
        if not self.client or not self.api_key:
            print("⚠️  Groq API not configured - using extractive fallback")
            return ' '.join(sentences[:3])
        
        # Build prompt
        prompt = self._build_prompt(sentences, context, style)
        
        print(f"\n{'='*60}")
        print(f"🤖 Calling Groq API")
        print(f"Model: {self.settings.LLM_MODEL}")
        print(f"Sentences to summarize: {len(sentences)}")
        print(f"{'='*60}")
        
        try:
            # Call Groq API
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.settings.LLM_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional assistant that summarizes customer support content concisely and clearly."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.settings.LLM_MAX_TOKENS,
                    "temperature": self.settings.LLM_TEMPERATURE,
                    "top_p": 1,
                    "stream": False
                }
            )
            
            # Check response status
            if response.status_code != 200:
                error_text = response.text
                print(f"❌ Groq API error {response.status_code}: {error_text}")
                raise Exception(f"Groq API returned {response.status_code}: {error_text}")
            
            result = response.json()
            
            # Extract summary from response
            summary = result['choices'][0]['message']['content']
            
            print(f"✅ Groq API call successful")
            print(f"Summary length: {len(summary)} characters")
            print(f"{'='*60}\n")
            
            return summary.strip()
        
        except httpx.HTTPStatusError as e:
            print(f"❌ Groq API HTTP error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
            raise Exception(f"Groq API error: {e.response.status_code} - {e.response.text}")
        
        except httpx.ConnectError as e:
            print(f"❌ Connection error to Groq API: {e}")
            raise Exception("Cannot connect to Groq API. Check your internet connection.")
        
        except KeyError as e:
            print(f"❌ Unexpected response format from Groq API: {e}")
            print(f"Response: {result if 'result' in locals() else 'N/A'}")
            raise Exception(f"Groq API returned unexpected format: {e}")
        
        except Exception as e:
            print(f"❌ Groq API error: {type(e).__name__}: {str(e)}")
            raise Exception(f"Groq API failed: {str(e)}")
    
    def _build_prompt(self, sentences: List[str], context: Optional[str],
                     style: str) -> str:
        """
        Build prompt for LLM
        
        Args:
            sentences: Extracted sentences
            context: Optional context
            style: Summary style
            
        Returns:
            Formatted prompt
        """
        content = '\n'.join(f"- {s}" for s in sentences)
        
        if style == "concise":
            instruction = "Create a concise 2-3 sentence summary"
        elif style == "detailed":
            instruction = "Create a detailed paragraph summary"
        elif style == "bullet":
            instruction = "Create a bullet-point summary"
        else:
            instruction = "Create a clear summary"
        
        prompt = f"""{instruction} of the following customer support content:

{content}"""
        
        if context:
            prompt += f"\n\nAdditional context:\n{context}"
        
        prompt += """

Focus on:
1. The main issue or request
2. Key actions taken or recommended
3. The resolution or current status

Keep the summary professional and clear. Output only the summary, no preamble."""
        
        return prompt
    
    async def generate_with_format(self, sentences: List[str],
                                   format_template: str) -> str:
        """Generate summary with specific format"""
        if not self.client or not self.api_key:
            return ' '.join(sentences[:3])
        
        prompt = f"""Format the following customer support information according to this template:

{format_template}

Key information:
{chr(10).join(f"- {s}" for s in sentences)}

Provide a concise, well-structured response. Output only the formatted content."""
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant for formatting customer support content."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.settings.LLM_MAX_TOKENS,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error in generate_with_format: {e}")
            return ' '.join(sentences[:3])
    
    async def extract_action_items(self, text: str) -> List[str]:
        """Extract action items from support text"""
        if not self.client or not self.api_key:
            return []
        
        prompt = f"""Extract clear, actionable items from this customer support content. List each as a separate bullet point.

{text}

Return only the action items as a numbered list, one per line. Be specific and concise."""
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You extract actionable items from text."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            result = response.json()
            text_response = result['choices'][0]['message']['content']
            
            items = []
            for line in text_response.split('\n'):
                line = line.strip()
                line = line.lstrip('0123456789.-) ')
                if line:
                    items.append(line)
            
            return items[:10]
        except Exception as e:
            print(f"Error extracting action items: {e}")
            return []
    
    async def classify_urgency(self, text: str) -> dict:
        """Classify urgency level of support request"""
        if not self.client or not self.api_key:
            return {"level": "medium", "reasoning": "Unable to classify"}
        
        prompt = f"""Analyze the urgency of this customer support request. 

Support content:
{text[:500]}

Respond in JSON format with:
- "level": one of ["low", "medium", "high", "critical"]
- "reasoning": brief explanation (1 sentence)

Output only the JSON, nothing else."""
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You classify support ticket urgency. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            result = response.json()
            response_text = result['choices'][0]['message']['content'].strip()
            
            try:
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                urgency_data = json.loads(response_text)
                return urgency_data
            except json.JSONDecodeError:
                text_lower = response_text.lower()
                if "critical" in text_lower:
                    level = "critical"
                elif "high" in text_lower:
                    level = "high"
                elif "low" in text_lower:
                    level = "low"
                else:
                    level = "medium"
                
                return {"level": level, "reasoning": response_text}
        except Exception as e:
            print(f"Error classifying urgency: {e}")
            return {"level": "medium", "reasoning": "Classification failed"}
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()