# SEC Finance agents

SEC Finance agents is an AI-powered chatbot designed to assist users with buying and selling stocks. It uses a state graph to manage the flow of conversation, leveraging advanced language models for decision-making.

---

## Features

- **Dynamic Routing**: The chatbot routes users based on their intention (e.g., buying, selling).
- **State Management**: Uses a `StateGraph` to track the user's messages and details.
- **Interactive Agents**: 
  - Supervisor Agent
  - Seller Agent
  - Buyer Agent
  - Confirmation Agent
- **Customizable Prompts**: System prompts can be tailored to suit specific business needs.

---

## Prerequisites

- **Python**: Ensure you have Python 3.8 or higher installed.
- **Dependencies**:
  Install dependencies listed in the `requirements.txt` file using pip:
  ```bash
  pip install -r requirements.txt
