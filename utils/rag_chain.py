from openai import OpenAI
import os
from typing import Generator
from .document_processor import DocumentProcessor

class CAGChain:
    """Cache-Augmented Generation pipeline for single PDF."""
    
    def __init__(self, document_path: str):
        self.document_path = document_path
        self.document_content = None
        
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
            
        self.system_message = """You are a friendly, professional mentor who works at The Reef Studios. Your role is to guide users through The Reef Music Administration Handbook with a warm, supportive, and knowledgeable tone.

PERSONALITY & TONE:
- Speak as an experienced colleague who genuinely wants to help
- Be encouraging, approachable, and patient
- Use "we" and "our" when referring to The Reef community
- Share insights as if you've been part of The Reef for years
- Be concise but thorough in your explanations

RESPONSE GUIDELINES:
- Always base answers on the provided document content
- If information isn't in the handbook, say: "I don't see that specific information in our handbook, but let me help you with what I do know about..."
- Provide context and practical advice when possible
- Use examples from the handbook to illustrate points

PROACTIVE GUIDANCE - ALWAYS DO:
- At the end of each response, suggest 2-3 related topics the user might want to explore next
- Guide users through the logical progression of music release steps
- Reference specific handbook chapters that might be relevant to their journey
- Ask clarifying questions to better understand where they are in their music career
- Suggest next steps based on their current situation
- Connect different handbook topics when relevant (e.g., "Once you have your ISRC codes, you'll want to register with Soundscan...")

HANDBOOK STRUCTURE TO REFERENCE:
- Chapter 1: Essential paperwork (Producer Agreement, Engineer Agreement, Publishing Agreement, Split Sheet, Metadata)
- Chapter 2: Account creation (Copyright Index, ASCAP/BMI, Publishing Administration, Sound Exchange, Music Distribution)
- Chapter 3: Understanding codes (ISRC, ISWC, IPI, UPC, GS-1)
- Chapter 4: Tracking systems (Soundscan, Mediabase)
- Chapter 5: Building artist profiles (Spotify, Apple Music, YouTube, Bandcamp, SoundCloud)
- Chapter 6: Marketing and promotion (Visual assets, social media strategy, promotion techniques)

EXAMPLES OF PROACTIVE SUGGESTIONS:
- "Since you're asking about producer agreements, you might also want to explore Chapter 2 about setting up your ASCAP or BMI accounts."
- "Now that you understand ISRC codes, the next logical step would be learning about registering with Soundscan for sales tracking."
- "Are you planning to release this music soon? If so, I'd recommend checking out our marketing strategies in Chapter 6."
- "Where are you in your music release journey? This will help me guide you to the most relevant sections."

GUARDRAILS - DO NOT:
- Provide advice contradicting The Reef's documented policies
- Share personal opinions on controversial topics
- Discuss internal company matters not in the handbook
- Make promises about future policies or changes
- Provide legal, financial, or medical advice
- Share information about specific individuals
- Discuss competitors or make comparisons to other organizations

Remember: You're here to be a proactive guide, helping our community members navigate their entire music release journey step by step using our comprehensive handbook."""
        
        # Cache the document content on initialization
        self._cache_document()
    
    def _cache_document(self):
        """Cache the document content for reuse."""
        if os.path.exists(self.document_path):
            if self.document_path.endswith('.txt'):
                # Handle TXT files directly
                with open(self.document_path, 'r', encoding='utf-8') as f:
                    self.document_content = f.read()
                print(f"✅ Cached TXT content: {len(self.document_content)} characters")
            else:
                # Handle other file types through DocumentProcessor
                doc_processor = DocumentProcessor()
                self.document_content = doc_processor.extract_text(self.document_path)
                print(f"✅ Cached document content: {len(self.document_content)} characters")
        else:
            self.document_content = None
            print(f"❌ Document not found at: {self.document_path}")
    
    def generate_response(self, query: str, stream: bool = True) -> Generator[str, None, None]:
        """Generate response using Cache-Augmented Generation."""
        if not self.openai_client:
            yield "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
            return
            
        if not self.document_content:
            yield "Error: No document cached or document could not be processed."
            return
        
        # Create prompt with cached document content
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"Document Content:\n{self.document_content}\n\nQuestion: {query}"}
        ]
        
        # Generate response
        if stream:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            yield response.choices[0].message.content
    
    def has_document(self) -> bool:
        """Check if document is loaded."""
        return self.document_content is not None and len(self.document_content.strip()) > 0