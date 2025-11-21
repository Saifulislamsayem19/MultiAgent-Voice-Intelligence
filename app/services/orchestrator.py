"""
Orchestrator Agent - Routes queries to appropriate specialized agents
"""
import logging
from typing import Dict, Any, Optional
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from app.config import settings, ORCHESTRATOR_CONFIG

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Master orchestrator for routing queries to specialized agents"""
    
    def __init__(self):
        """Initialize orchestrator agent"""
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.3  # Lower temperature for more consistent routing
        )
        
        self.system_prompt = ORCHESTRATOR_CONFIG["system_prompt"]
        
        # Create routing prompt
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """
                Analyze the following query and determine which agent(s) should handle it.

                IMPORTANT: Follow these routing rules:
                - Weather, time, calculations, greetings -> "general"
                - Health, medical, symptoms -> "medical"
                - AI, ML, neural networks, algorithms -> "ai_ml"
                - Property, real estate, housing -> "real_estate"
                - Sales, customers, revenue -> "sales"
                - Learning, education, teaching -> "education"

                Respond with a JSON object containing:
                - "primary_agent": The main agent to handle this query
                - "secondary_agents": List of other agents that might provide supporting information (optional)
                - "reasoning": Brief explanation of why this agent was chosen
                - "confidence": Confidence score from 0 to 1

                Query: {query}

                Response (JSON only):
                """)
        ])
    
    async def route_query(self, query: str) -> str:
        """
        Route a query to the appropriate agent
        
        Args:
            query: User query to route
            
        Returns:
            Name of the selected agent
        """
        try:
            # Check for specific keywords that should go to general agent
            general_keywords = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 
                              'calculate', 'math', 'time', 'timezone', 'what time',
                              'hello', 'hi', 'how are you', 'thank']
            
            query_lower = query.lower()
            
            # Quick routing for obvious cases
            if any(keyword in query_lower for keyword in general_keywords):
                logger.info(f"Routing to general agent for query: {query[:50]}...")
                return "general"
            
            # Check for medical keywords
            medical_keywords = ['sick', 'ill', 'pain', 'symptom', 'disease', 'health', 
                              'medical', 'doctor', 'medicine', 'treatment', 'diagnosis']
            if any(keyword in query_lower for keyword in medical_keywords):
                logger.info(f"Routing to medical agent for query: {query[:50]}...")
                return "medical"
            
            # Check for AI/ML keywords
            ai_keywords = ['ai', 'ml', 'machine learning', 'neural', 'deep learning',
                          'model', 'algorithm', 'training', 'dataset', 'tensorflow',
                          'pytorch', 'scikit', 'nlp', 'computer vision']
            if any(keyword in query_lower for keyword in ai_keywords):
                logger.info(f"Routing to ai_ml agent for query: {query[:50]}...")
                return "ai_ml"
            
            # Check for real estate keywords
            real_estate_keywords = ['property', 'house', 'apartment', 'real estate',
                                   'mortgage', 'rent', 'buy house', 'sell house']
            if any(keyword in query_lower for keyword in real_estate_keywords):
                logger.info(f"Routing to real_estate agent for query: {query[:50]}...")
                return "real_estate"
            
            # Check for sales keywords
            sales_keywords = ['sales', 'customer', 'client', 'revenue', 'deal',
                            'lead', 'crm', 'pipeline', 'quota', 'prospect']
            if any(keyword in query_lower for keyword in sales_keywords):
                logger.info(f"Routing to sales agent for query: {query[:50]}...")
                return "sales"
            
            # Check for education keywords
            education_keywords = ['learn', 'study', 'education', 'course', 'teach',
                                'school', 'university', 'exam', 'homework', 'curriculum']
            if any(keyword in query_lower for keyword in education_keywords):
                logger.info(f"Routing to education agent for query: {query[:50]}...")
                return "education"
            
            # If no specific match, use LLM for routing
            messages = self.routing_prompt.format_messages(query=query)
            response = await self.llm.ainvoke(messages)
            
            # Parse response
            try:
                # Extract JSON from response
                response_text = response.content
                
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    routing_decision = json.loads(json_match.group())
                else:
                    # Default to general agent
                    logger.warning(f"Could not parse routing response: {response_text}")
                    return "general"
                
                primary_agent = routing_decision.get("primary_agent", "general")
                confidence = routing_decision.get("confidence", 0)
                reasoning = routing_decision.get("reasoning", "")
                
                logger.info(f"Routing decision: {primary_agent} (confidence: {confidence}) - {reasoning}")
                
                # Validate agent name
                valid_agents = ["general", "real_estate", "medical", "ai_ml", "sales", "education"]
                if primary_agent not in valid_agents:
                    logger.warning(f"Invalid agent name: {primary_agent}, using general")
                    return "general"
                
                return primary_agent
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing routing response: {str(e)}")
                return "general"  # Default fallback
                
        except Exception as e:
            logger.error(f"Error in route_query: {str(e)}")
            return "general"  # Default fallback
    
    async def coordinate_multi_agent_response(
        self,
        query: str,
        primary_agent_response: str,
        secondary_responses: Dict[str, str]
    ) -> str:
        """
        Coordinate responses from multiple agents
        
        Args:
            query: Original user query
            primary_agent_response: Response from primary agent
            secondary_responses: Responses from secondary agents
            
        Returns:
            Coordinated response
        """
        try:
            # Create coordination prompt
            coord_prompt = f"""
                You are coordinating responses from multiple specialized agents for this query: {query}

                Primary response (main answer):
                {primary_agent_response}

                Additional context from other agents:
                """
            for agent, response in secondary_responses.items():
                coord_prompt += f"\n{agent}: {response}\n"
            
            coord_prompt += """
                Please synthesize these responses into a comprehensive, coherent answer that:
                1. Prioritizes the primary response
                2. Incorporates relevant additional context
                3. Maintains consistency and accuracy
                4. Provides a natural, unified response

                Synthesized response:
                """
            
            # Get coordinated response
            messages = [
                SystemMessage(content="You are a response coordinator that synthesizes multiple expert opinions into coherent answers."),
                HumanMessage(content=coord_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error coordinating responses: {str(e)}")
            return primary_agent_response  # Fallback to primary response
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """
        Analyze query complexity to determine if multi-agent coordination is needed
        
        Args:
            query: User query to analyze
            
        Returns:
            Analysis results including complexity score and recommended approach
        """
        try:
            # Simple heuristics for complexity analysis
            complexity_indicators = {
                "multi_domain": False,
                "comparison": False,
                "technical_depth": False,
                "requires_context": False
            }
            
            # Check for multi-domain indicators
            domain_keywords = {
                "real_estate": ["property", "house", "apartment", "mortgage", "real estate"],
                "medical": ["health", "medical", "symptom", "treatment", "disease"],
                "ai_ml": ["AI", "machine learning", "neural", "algorithm", "model"],
                "sales": ["sales", "customer", "revenue", "marketing", "lead"],
                "education": ["learn", "study", "course", "education", "teach"]
            }
            
            domains_mentioned = []
            for domain, keywords in domain_keywords.items():
                if any(keyword.lower() in query.lower() for keyword in keywords):
                    domains_mentioned.append(domain)
            
            if len(domains_mentioned) > 1:
                complexity_indicators["multi_domain"] = True
            
            # Check for comparison keywords
            comparison_words = ["compare", "versus", "vs", "difference", "better", "choose"]
            if any(word in query.lower() for word in comparison_words):
                complexity_indicators["comparison"] = True
            
            # Check for technical depth
            technical_words = ["implement", "architecture", "optimize", "integrate", "develop"]
            if any(word in query.lower() for word in technical_words):
                complexity_indicators["technical_depth"] = True
            
            # Calculate complexity score
            complexity_score = sum(complexity_indicators.values()) / len(complexity_indicators)
            
            return {
                "complexity_score": complexity_score,
                "indicators": complexity_indicators,
                "domains_mentioned": domains_mentioned,
                "requires_multi_agent": complexity_score > 0.5 or len(domains_mentioned) > 1
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query complexity: {str(e)}")
            return {
                "complexity_score": 0,
                "indicators": {},
                "domains_mentioned": [],
                "requires_multi_agent": False
            }
