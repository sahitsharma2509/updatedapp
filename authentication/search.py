from langchain.llms import OpenAI
from langchain.agents import initialize_agent,Tool,load_tools
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory,ConversationSummaryMemory
from langchain.memory import ConversationTokenBufferMemory,ConversationBufferWindowMemory
from langchain.utilities import GoogleSearchAPIWrapper,GoogleSerperAPIWrapper
from langchain.chat_models import ChatOpenAI
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.memory import ChatMessageHistory
import time


import os 


os.environ['GOOGLE_CSE_ID'] = "71569d2dba74540d9"
os.environ['GOOGLE_API_KEY']="AIzaSyAIqeLS5pxxx2iq52GkV3g_1AZzSwdRxa8"
os.environ['SERPER_API_KEY']='3d856dbf3811b58136f49fd8ccfcac3c80bd3f22bacff9f9fec7f10fdcee11c3'
os.environ["WOLFRAM_ALPHA_APPID"] = "X4LW2T-EXEGW5E7T6"
os.environ["OPENAI_API_KEY"] = "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"
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper

search = GoogleSearchAPIWrapper()
serp_search = GoogleSerperAPIWrapper()
wolfram = WolframAlphaAPIWrapper()

tools = [
     Tool(
        name = "Google search",
        func=search.run,
        description="useful for when you need to answer questions about current events from Google."
    ),
     Tool(
        name = "Serp search",
        func=serp_search.run,
        description="Use it if google is unable to answer the question."
    ),
      Tool(
        name = "wolfram search",
        func=wolfram.run,
        description="useful for when you need to do math."
    )
   
]

#memory = ConversationBufferMemory(memory_key="chat_history")



llm = OpenAI(temperature=0,verbose=True)

#memory = ConversationTokenBufferMemory(llm=llm, max_token_limit=100,return_messages=True,memory_key="chat_history")
#memory = ConversationBufferWindowMemory(k=7,memory_key="chat_history")
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
agent_chain = initialize_agent(tools,llm, agent="conversational-react-description", memory=memory, verbose = True)
chat_history = ConversationBufferMemory()
#history = ChatMessageHistory()

def qsearch(query):
    print(f"qsearch called with query: {query}")  # Add print statement
    output = agent_chain.run(input=query)
    print(f"Agent chain output: {output}")  # Add print statement
    memory.chat_memory.add_user_message(query)
    memory.chat_memory.add_ai_message(output)
    chat_history.chat_memory.add_user_message(query)
    chat_history.chat_memory.add_ai_message(output)

    history_llm = memory.load_memory_variables({})
    history_chat = chat_history.load_memory_variables({})
    output = {"output": output, "history": history_chat['history']}

    

    

    return output

   





