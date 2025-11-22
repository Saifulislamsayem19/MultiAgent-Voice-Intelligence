"""
Specialized Agents - Domain-specific agents for different knowledge areas
"""
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool, StructuredTool
from langchain.schema import SystemMessage, HumanMessage

from app.config import settings, AGENT_CONFIGS
from app.services.vector_store import VectorStoreService
from app.services.tools import WeatherTool, CalculatorTool, TimezoneTool, WebSearchTool

logger = logging.getLogger(__name__)

class BaseSpecializedAgent(ABC):
    """Base class for specialized agents"""
    
    def __init__(self, agent_name: str):
        """Initialize base specialized agent"""
        self.agent_name = agent_name
        self.config = AGENT_CONFIGS.get(agent_name, {})
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.temperature
        )
        
        # Initialize vector store service
        self.vector_store_service = VectorStoreService()
        
        # Get tools for this agent
        self.tools = self._get_tools()
        
        # Create agent prompt
        self.prompt = self._create_prompt()
        
        # Create agent executor
        self.agent = self._create_agent()
    
    @abstractmethod
    def _get_tools(self) -> List[Tool]:
        """Get tools specific to this agent"""
        pass
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for the agent"""
        system_prompt = self.config.get("system_prompt", "You are a helpful assistant.")
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _create_agent(self) -> AgentExecutor:
        """Create agent executor"""
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=settings.max_iterations,
            handle_parsing_errors=True
        )
    
    async def process_query(
        self,
        query: str,
        memory: Optional[ConversationBufferMemory] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Process a query using the specialized agent
        
        Args:
            query: User query
            memory: Conversation memory
            include_sources: Whether to include source documents
            
        Returns:
            Agent response with metadata
        """
        try:
            # Retrieve relevant documents
            sources = []
            context = ""
            
            if include_sources:
                search_results = self.vector_store_service.search(
                    agent=self.agent_name,
                    query=query,
                    k=5
                )
                
                if search_results:
                    context = "\n\nRelevant information from knowledge base:\n"
                    for doc, score in search_results:
                        context += f"\n- {doc.page_content[:500]}..."
                        sources.append({
                            "content": doc.page_content[:200],
                            "metadata": doc.metadata,
                            "score": float(score)
                        })
            
            # Prepare input with context
            enhanced_query = query
            if context:
                enhanced_query = f"{query}\n{context}"
            
            # Get chat history if memory provided
            chat_history = []
            if memory:
                chat_history = memory.chat_memory.messages
            
            # Process with agent
            response = await self.agent.ainvoke({
                "input": enhanced_query,
                "chat_history": chat_history
            })
            
            # Update memory
            if memory:
                memory.chat_memory.add_user_message(query)
                memory.chat_memory.add_ai_message(response["output"])
            
            return {
                "response": response["output"],
                "sources": sources if include_sources else None,
                "agent": self.agent_name,
                "tokens_used": 0  
            }
            
        except Exception as e:
            logger.error(f"Error processing query in {self.agent_name}: {str(e)}")
            raise

class GeneralAgent(BaseSpecializedAgent):
    """Agent for general queries, weather, calculations, etc."""
    
    def __init__(self):
        super().__init__("general")
    
    def _get_tools(self) -> List[Tool]:
        """Get general tools"""
        tools = []
        
        # Add all general-purpose tools
        tools.append(WeatherTool().as_tool())
        tools.append(CalculatorTool().as_tool())
        tools.append(TimezoneTool().as_tool())
        tools.append(WebSearchTool().as_tool())
        
        return tools

class RealEstateAgent(BaseSpecializedAgent):
    """Agent specialized in real estate topics"""
    
    def __init__(self):
        super().__init__("real_estate")
    
    def _get_tools(self) -> List[Tool]:
        """Get real estate specific tools"""
        tools = []
        
        # Property search tool
        tools.append(Tool(
            name="property_search",
            func=self._property_search,
            description="Search for property information and listings"
        ))
        
        # Market analysis tool
        tools.append(Tool(
            name="market_analysis",
            func=self._market_analysis,
            description="Analyze real estate market trends and data"
        ))
        
        # Add general tools
        tools.append(WeatherTool().as_tool())
        tools.append(CalculatorTool().as_tool())
        
        return tools
    
    def _property_search(self, query: str) -> str:
        """Mock property search implementation"""
        return f"Property search results for: {query}"
    
    def _market_analysis(self, location: str) -> str:
        """Mock market analysis implementation"""
        return f"Market analysis for {location}: Average prices, trends, etc."

class MedicalAgent(BaseSpecializedAgent):
    """Agent specialized in medical and health topics"""
    
    def __init__(self):
        super().__init__("medical")
    
    def _get_tools(self) -> List[Tool]:
        """Get medical specific tools"""
        tools = []
        
        # Symptom checker tool
        tools.append(Tool(
            name="symptom_checker",
            func=self._symptom_checker,
            description="Check symptoms and provide general health information"
        ))
        
        # Add general tools
        tools.append(CalculatorTool().as_tool())
        
        return tools
    
    def _symptom_checker(self, symptoms: str) -> str:
        """Mock symptom checker implementation"""
        return f"Based on symptoms '{symptoms}', please consult a healthcare professional for accurate diagnosis."

class AIMLAgent(BaseSpecializedAgent):
    """Agent specialized in AI/ML topics"""
    
    def __init__(self):
        super().__init__("ai_ml")
    
    def _get_tools(self) -> List[Tool]:
        """Get AI/ML specific tools"""
        tools = []
        
        # Code examples tool
        tools.append(Tool(
            name="code_examples",
            func=self._get_code_examples,
            description="Get code examples for AI/ML implementations"
        ))
        
        # Model recommendations tool
        tools.append(Tool(
            name="model_recommendations",
            func=self._recommend_models,
            description="Recommend ML models for specific use cases"
        ))
        
        # Add general tools
        tools.append(CalculatorTool().as_tool())
        
        return tools
    
    def _get_code_examples(self, topic: str) -> str:
        """Get code examples for a topic"""
        return f"Here's a code example for {topic}: [Code implementation would go here]"
    
    def _recommend_models(self, use_case: str) -> str:
        """Recommend models for a use case"""
        return f"For {use_case}, consider these models: [Model recommendations]"

class SalesAgent(BaseSpecializedAgent):
    """Agent specialized in sales and business development"""
    
    def __init__(self):
        super().__init__("sales")
    
    def _get_tools(self) -> List[Tool]:
        """Get sales specific tools"""
        tools = []
        
        # CRM insights tool
        tools.append(Tool(
            name="crm_insights",
            func=self._get_crm_insights,
            description="Get CRM insights and customer data analysis"
        ))
        
        # Sales metrics tool
        tools.append(Tool(
            name="sales_metrics",
            func=self._calculate_sales_metrics,
            description="Calculate and analyze sales metrics"
        ))
        
        # Add general tools
        tools.append(CalculatorTool().as_tool())
        
        return tools
    
    def _get_crm_insights(self, query: str) -> str:
        """Get CRM insights"""
        return f"CRM insights for {query}: [Customer data analysis]"
    
    def _calculate_sales_metrics(self, data: str) -> str:
        """Calculate sales metrics"""
        return f"Sales metrics calculated: [Conversion rates, revenue, etc.]"

class EducationAgent(BaseSpecializedAgent):
    """Agent specialized in education and learning"""
    
    def __init__(self):
        super().__init__("education")
    
    def _get_tools(self) -> List[Tool]:
        """Get education specific tools"""
        tools = []
        
        # Study planner tool
        tools.append(Tool(
            name="study_planner",
            func=self._create_study_plan,
            description="Create personalized study plans"
        ))
        
        # Resource finder tool
        tools.append(Tool(
            name="resource_finder",
            func=self._find_resources,
            description="Find educational resources and materials"
        ))
        
        # Add general tools
        tools.append(CalculatorTool().as_tool())
        
        return tools
    
    def _create_study_plan(self, subject: str) -> str:
        """Create a study plan"""
        return f"Study plan for {subject}: [Structured learning path]"
    
    def _find_resources(self, topic: str) -> str:
        """Find educational resources"""
        return f"Educational resources for {topic}: [Books, courses, videos, etc.]"

class SpecializedAgentFactory:
    """Factory for creating specialized agents"""
    
    def __init__(self):
        """Initialize agent factory"""
        self.agents = {
            "general": GeneralAgent,
            "real_estate": RealEstateAgent,
            "medical": MedicalAgent,
            "ai_ml": AIMLAgent,
            "sales": SalesAgent,
            "education": EducationAgent
        }
        
        # Cache for initialized agents
        self._agent_cache = {}
    
    def get_agent(self, agent_name: str) -> BaseSpecializedAgent:
        """
        Get a specialized agent by name
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Initialized specialized agent
        """
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Check cache
        if agent_name not in self._agent_cache:
            agent_class = self.agents[agent_name]
            self._agent_cache[agent_name] = agent_class()
        
        return self._agent_cache[agent_name]
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with descriptions"""
        available = []
        for name in self.agents.keys():
            config = AGENT_CONFIGS.get(name, {})
            available.append({
                "name": name,
                "display_name": config.get("name", name),
                "description": config.get("description", ""),
                "tools": config.get("tools", [])
            })
        return available
