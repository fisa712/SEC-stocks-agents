# imports
import json
import os
from typing import Dict, Annotated

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from prompts import master_system, buyer_system, confirmation_system, seller_system

# Load the .env file
load_dotenv()

# Access the API key
os.getenv("GROQ_API_KEY")


# Extend State to include tasks
class State(TypedDict):
    messages: Annotated[list, add_messages]
    details: Dict  # Add tasks to the state


# class
class Graph:
    def __init__(self, state: State, model_name="llama-3.3-70b-versatile", temperature=0):
        self.llm = ChatGroq(temperature=temperature, model_name=model_name)
        self.new_messages = []
        # self.details = state.get('details', {})
        self.graph_builder = StateGraph(State)
        self.graph_builder.add_conditional_edges(
            "chatbot",
            self.router,

            {
                "selling": "seller",
                "buying": "buyer",
                END: END
            }, then="confirmation_agent"
        )

        # Add the chatbot node and set entry/finish points
        self.graph_builder.add_node("chatbot", self.supervisor_agent)
        self.graph_builder.add_node("seller", self.seller_agent)
        self.graph_builder.add_node("buyer", self.buyer_agent)
        self.graph_builder.add_node('confirmation_agent', self.confirmation_agent)
        self.graph_builder.set_entry_point("chatbot")
        self.graph_builder.set_finish_point("confirmation_agent")
        self.graph = self.graph_builder.compile()

    def build_chain(self, system_prompt, human_input="{text}"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", human_input)
            ]
        )
        chain = prompt | self.llm
        return chain

    def router(self, state: State):
        details = state["details"]
        if next := details.get('intention', None):
            if "sell" in next:
                return "selling"
            elif "buy" in next:
                return "buying"
            else:
                raise "Something went wrong here at router"
        else:
            return END

    def supervisor_agent(self, state: State):
        details = state["details"]
        self.new_messages = state.get("messages", [])
        model = self.build_chain(master_system)
        response = model.invoke(
            {"text": self.new_messages}
        )  # {"text": "hi i want to invest in stocks."}
        data = ("system", response.content)
        self.new_messages.append(data)
        try:
            cleaned_json_string = response.content.strip('```json').strip('```').strip("\n")
            json_response = json.loads(cleaned_json_string)
        except:
            print("*" * 50)
            print(response.content)
            print("*" * 50)

        else:

            details['name'] = json_response.get('user_name')
            details['email'] = json_response.get('email')
            details['phone'] = json_response.get('phone')
            details['intention'] = json_response.get('intention')
            details['stock_symbol'] = json_response.get('stock_symbol')
            # something else:

        return {
            # "messages": self.new_messages[-1],
            "details": details
        }

    def seller_agent(self, state: State):  #
        self.new_messages = state.get("messages", [])
        old_messages_count = len(self.new_messages)
        details = state["details"]
        plans = ['x', 'y', 'z']
        model = self.build_chain(seller_system)
        while True:
            response = model.invoke({"text": self.new_messages})

            try:
                # cleaned_json_string = res.content.strip('```json').strip('```').strip()
                json_response = json.loads(response.content.strip())
                if json_response.get('plan').lower() in plans:  # and json_final_res.get('user_intention') != 'stay':
                    msg = json_response.get('message')
                    print("*" * 50)
                    print("Seller (json): ", msg)
                    print("*" * 50)

                    data = [("system", response.content)]
                    # state.get("messages", []).extend(data)
                    self.new_messages.extend(data)

                    details['plan'] = json_response.get('plan')
                    break
            except:
                print("*" * 50)
                print("Seller: ", response.content)
                print("*" * 50)

                human_input = input("->")

                data = [("system", response.content), ("user", human_input)]
                # state.get("messages", []).extend(data)
                self.new_messages.extend(data)
        upd = self.new_messages[old_messages_count:]
        return {
            # "messages": self.new_messages[old_messages_count:],
            "details": details,
        }

    def buyer_agent(self, state: State):
        self.new_messages = state.get("messages", [])
        old_messages_count = len(self.new_messages)
        details = state["details"]
        plans = ['a', 'b', 'c']
        model = self.build_chain(buyer_system)
        while True:
            response = model.invoke({"text": self.new_messages})
            self.new_messages.append(("system", response.content))
            try:
                # cleaned_json_string = response.content.strip('```json').strip('```').strip()

                json_response = json.loads(response.content.strip())
                if json_response.get('plan').lower() in plans:  # and json_final_res.get('user_intention') != 'stay':
                    msg = json_response.get('message')

                    print("*" * 50)
                    print("Buyer (json): ", msg)
                    print("*" * 50)
                    # data = [("system", msg)]
                    # state.get("messages", []).extend(data)

                    # self.new_messages.extend(data)

                    details['plan'] = json_response.get('plan')
                    break

            except:
                print("*" * 50)
                print("Buyer: ", response.content)
                print("*" * 50)

                human_input = input("->")

                data = ("user", human_input)
                # state.get("messages", []).extend(data)
                self.new_messages.append(data)

        # details['plan'] = json_response.get('plan')
        upd = self.new_messages[old_messages_count:]
        return {
            # "messages": self.new_messages[old_messages_count:],
            "details": details,
        }

    def confirmation_agent(self, state: State):
        self.new_messages = state.get("messages", [])
        old_messages_count = len(self.new_messages)
        details = state["details"]
        model = self.build_chain(confirmation_system)
        while True:
            response = model.invoke({"text": self.new_messages, "details": details})
            try:
                json_res = json.loads(response.content.strip())
                confirmation = json_res.get('details_confirmed')
                allowed = ['yes', "true"]
                if confirmation.lower() in allowed:
                    # details = state["details"]
                    details['details_confirmed'] = confirmation
                    print("congrats! you have gained the plan for the stocks.")
                    print("*" * 50)

                    data = [("system", response.content)]
                    self.new_messages.extend(data)
                    break
            except:
                print("*" * 50)
                print("Conf Agent: ", response.content)
                print("*" * 50)
                human_input = input("->")

                data = [("system", response.content), ("user", human_input)]
                self.new_messages.extend(data)

        return {
            # "messages": self.new_messages[old_messages_count:],
            "details": details,
        }


if __name__ == "__main__":

    while True:

        human_input = input("STARTING A CHAT>>> ")
        state = State(
            messages=[("user", human_input)],
            details={
                "name": None,
                "email": None,
                "phone": None,
                "intention": None,

                "stock_symbol": None,
                "details_confirmed": None})

        if human_input == "q":
            break
        graph = Graph(state).graph  # error
        graph.invoke(state)
