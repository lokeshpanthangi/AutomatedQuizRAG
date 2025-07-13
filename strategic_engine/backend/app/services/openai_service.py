import os
import openai
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key and self.api_key != "your_actual_openai_api_key":
            try:
                openai.api_key = self.api_key
                self.client = openai
                print("OpenAI client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        else:
            print("OpenAI API key not configured - AI features will be disabled")
        
        self.embedding_model = "text-embedding-ada-002"
        self.chat_model = "gpt-4"
        
        # Strategic business system prompt
        self.system_prompt = """
You are a strategic business advisor for CEOs and senior executives. Your role is to provide actionable, data-driven insights for strategic decision-making.

Guidelines:
1. Focus on business value and strategic implications
2. Provide specific, actionable recommendations
3. Always cite the source documents when making claims
4. Consider risks, opportunities, and resource requirements
5. Think like a management consultant with deep business expertise
6. Structure responses clearly with executive summaries when appropriate
7. Highlight key metrics, trends, and competitive advantages
8. Consider both short-term and long-term strategic implications

When analyzing documents, look for:
- Financial performance indicators
- Market opportunities and threats
- Operational efficiency metrics
- Competitive positioning
- Growth potential and scalability
- Risk factors and mitigation strategies
"""
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if not self.client:
            print("OpenAI client not available - cannot generate embeddings")
            return None
            
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text.replace("\n", " ")
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently"""
        if not self.client:
            print("OpenAI client not available - cannot generate embeddings")
            return [None] * len(texts)
            
        embeddings = []
        batch_size = 100  # OpenAI recommended batch size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                # Clean texts
                cleaned_batch = [text.replace("\n", " ") for text in batch]
                
                response = openai.Embedding.create(
                    model=self.embedding_model,
                    input=cleaned_batch
                )
                
                batch_embeddings = [item['embedding'] for item in response['data']]
                embeddings.extend(batch_embeddings)
                
                # Small delay to respect rate limits
                if i + batch_size < len(texts):
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {str(e)}")
                # Return None for failed embeddings
                embeddings.extend([None] * len(batch))
        
        return embeddings
    
    def analyze_query_intent(self, query: str) -> Dict[str, str]:
        """Analyze query to determine intent and extract key concepts"""
        if not self.client:
            print("OpenAI client not available - using fallback analysis")
            return {
                'intent': 'general analysis',
                'concepts': 'business strategy',
                'relevant types': 'general'
            }
            
        intent_prompt = f"""
Analyze this business query and extract:
1. Primary intent (analysis, recommendation, comparison, evaluation, etc.)
2. Key business concepts mentioned
3. Suggested document types that would be most relevant

Query: "{query}"

Respond in this format:
Intent: [primary intent]
Concepts: [key concepts separated by commas]
Relevant Types: [document types separated by commas]
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use faster model for intent analysis
                messages=[
                    {"role": "system", "content": "You are a business analyst expert at understanding strategic queries."},
                    {"role": "user", "content": intent_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            # Parse the response
            lines = analysis.strip().split('\n')
            result = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip().lower()] = value.strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing query intent: {str(e)}")
            return {
                'intent': 'general analysis',
                'concepts': 'business strategy',
                'relevant types': 'general'
            }
    
    def generate_strategic_response(self, query: str, context_chunks: List[Dict], sources: List[str]) -> str:
        """Generate strategic response using GPT-4 with context and citations"""
        if not self.client:
            return "I apologize, but the AI analysis service is currently not available. Please configure your OpenAI API key to enable strategic analysis features."
            
        # Prepare context from retrieved chunks
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            context_text += f"\n[Source {i+1}]: {chunk.get('text', '')}\n"
        
        # Prepare sources list
        sources_text = "\n".join([f"- {source}" for source in sources])
        
        # Create the prompt
        user_prompt = f"""
Based on the following company documents, please provide a strategic analysis for this question:

**Question:** {query}

**Available Context:**
{context_text}

**Source Documents:**
{sources_text}

**Instructions:**
1. Provide a comprehensive strategic analysis
2. Include specific recommendations with clear rationale
3. Cite specific sources when making claims (use [Source X] format)
4. Highlight key insights and strategic implications
5. Consider risks and opportunities
6. Structure your response with clear sections if appropriate

Please ensure your response is actionable and valuable for executive decision-making.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating strategic response: {str(e)}")
            return f"I apologize, but I encountered an error while generating the strategic analysis. Error: {str(e)}"
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.client:
            print("OpenAI client not available")
            return False
            
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False


# Example usage and testing
if __name__ == "__main__":
    try:
        service = OpenAIService()
        
        # Test connection
        if service.test_connection():
            print("✅ OpenAI connection successful!")
        else:
            print("❌ OpenAI connection failed!")
        
        # Test embedding generation
        sample_text = "This is a sample business document about revenue growth."
        embedding = service.generate_embedding(sample_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        # Test query intent analysis
        sample_query = "What are our main revenue drivers?"
        intent = service.analyze_query_intent(sample_query)
        print(f"✅ Query intent analysis: {intent}")
        
        print("\nOpenAI service initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing OpenAI service: {str(e)}")
        print("Please check your OPENAI_API_KEY in the .env file")