"""LangChain orchestrator for routing queries to specialist tools."""

from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config import get_settings
from src.orchestrator.prompts import ROUTING_SYSTEM_PROMPT, ROUTING_USER_PROMPT
from src.tools import FundFactsTool, RRSPTool, TFSATool
from src.tools.schemas import ChatResponse, OrchestratorDecision, ToolResponse


class RouterOutput(BaseModel):
    """Structured output for the router."""

    tool: Literal["tfsa", "rrsp", "fund_facts"] = Field(
        description="Which tool to route the query to"
    )
    generate_chart: bool = Field(
        default=False, description="Whether to generate a chart"
    )
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram"] = Field(
        default="bar", description="Type of chart to generate"
    )
    reasoning: str = Field(description="Brief explanation for the routing decision")


def get_llm():
    """
    Returns LangChain LLM based on environment.
    - Dev: Uses API key via langchain_google_genai
    - Prod: Uses Vertex AI via langchain_google_vertexai
    """
    settings = get_settings()

    if settings.is_dev():
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Use Flash for fast routing
            google_api_key=settings.google_api_key,
        )
    else:
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(
            model_name="gemini-1.5-flash",  # Use Flash for fast routing
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )


class Orchestrator:
    """Routes user queries to the appropriate specialist tool."""

    def __init__(self):
        self.tools = {
            "tfsa": TFSATool(),
            "rrsp": RRSPTool(),
            "fund_facts": FundFactsTool(),
        }
        self.llm = get_llm()
        self.parser = PydanticOutputParser(pydantic_object=RouterOutput)

        # Build the routing prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTING_SYSTEM_PROMPT + "\n\n{format_instructions}"),
            ("human", ROUTING_USER_PROMPT),
        ])

    def route(self, user_query: str) -> OrchestratorDecision:
        """
        Determine which tool should handle the query and chart parameters.

        Args:
            user_query: The user's message

        Returns:
            OrchestratorDecision with tool, chart params, and reasoning
        """
        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "user_query": user_query,
            "format_instructions": self.parser.get_format_instructions(),
        })

        return OrchestratorDecision(
            tool=result.tool,
            user_query=user_query,
            generate_chart=result.generate_chart,
            chart_type=result.chart_type,
            reasoning=result.reasoning,
        )

    def process(self, user_query: str) -> ChatResponse:
        """
        Process a user query end-to-end.

        Args:
            user_query: The user's message

        Returns:
            ChatResponse with reply, optional chart, and sources
        """
        # 1. Route the query
        decision = self.route(user_query)

        # 2. Get the appropriate tool
        tool = self.tools.get(decision.tool, self.tools["fund_facts"])

        # 3. Invoke the tool
        tool_response: ToolResponse = tool.invoke(
            user_query=decision.user_query,
            generate_chart=decision.generate_chart,
            chart_type=decision.chart_type,
        )

        # 4. Return as ChatResponse
        return ChatResponse(
            reply=tool_response.reply,
            chart_type=tool_response.chart_type,
            image_base64=tool_response.image_base64,
            sources=tool_response.sources,
        )
