from langchain.agents import (
    create_structured_chat_agent,
    AgentExecutor,
    tool,
)
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

from tests.mock_chat_model import MockChatModel


def test_from_prompt_model():

    @tool
    def add_numbers(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b

    @tool
    def multiply_numbers(a: int, b: int) -> int:
        """Multiplies two numbers."""
        return a * b

    # List of tools
    tools = [add_numbers, multiply_numbers]

    # Create the system and human prompts
    system_prompt = '''Respond to the human as helpfully and accurately as possible. You have access to the following tools:
    
    {tools}
    
    Use a JSON blob to specify a tool by providing an "action" key (tool name) and an "action_input" key (tool input).
    
    Valid "action" values: "Final Answer" or {tool_names}
    
    Provide only ONE action per JSON blob, as shown:
    
    {{ "action": $TOOL_NAME, "action_input": $INPUT }}
    
    Follow this format:
    
    Question: input question to answer
    Thought: consider previous and subsequent steps
    Action: $JSON_BLOB
    
    Observation: action result
    ... (repeat Thought/Action/Observation N times)
    Thought: I know what to respond
    Action: {{ "action": "Final Answer", "action_input": "Final response to human" }}
    
    
    Begin! Reminder to ALWAYS respond with a valid JSON blob of a single action. Use tools if necessary. 
    Respond directly if appropriate. Format is Action:```$JSON_BLOB``` then Observation'''

    human_prompt = '''{input}
    {agent_scratchpad}
    (Reminder to respond in a JSON blob no matter what)'''

    system_message = SystemMessagePromptTemplate.from_template(
        system_prompt,
        input_variables=["tools", "tool_names"],
    )
    human_message = HumanMessagePromptTemplate.from_template(
        human_prompt,
        input_variables=["input", "agent_scratchpad"],
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            system_message,
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            human_message,
        ]
    )

    llm = MockChatModel(
        api_key="API_KEY",
        base_url="BASE_URL",
        model="MODEL",
        temperature=0.5,
        max_tokens=3000,
    )

    # Create the structured chat agent
    agent = create_structured_chat_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        stop_sequence=True,
    )

    # Create the AgentExecutor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,  # Set to True if you want intermediate steps
        output_keys=["output"],
    )

    user_question = "What is the sum and product of 15 and 27?"

    response = agent_executor.invoke({"input": user_question})

    final_answer = response["output"]

    assert final_answer is not None