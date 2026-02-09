import requests
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv()

def commodity_chatbot(user_message, conversation_history=None):
    """
    ICMA - Intelligent Commodity Market Analyst chatbot
    """
    # Initialize conversation history if not provided
    if conversation_history is None:
        conversation_history = []

    # System prompt defines the chatbot's role and expertise
    system_prompt = {
        "role": "system",
        "content": """You are ICMA (Intelligent Commodity Market Analyst), an expert AI assistant specializing in commodity markets.

Your expertise includes:
- Analyzing commodity price trends (gold, oil, agricultural products, metals)
- Explaining market factors and geopolitical impacts
- Providing insights on supply and demand dynamics
- Helping users understand trading opportunities and risks

Be concise, professional, and actionable. Use data-driven insights when possible."""
    }

    # Build the messages array
    messages = [system_prompt] + conversation_history + [
        {"role": "user", "content": user_message}
    ]

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('CHATBOT_API_KEY')}",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Commodity Trading Chatbot",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-5-nano",
                "messages": messages
            },
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        ai_response = result['choices'][0]['message']['content']

        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append(
            {"role": "assistant", "content": ai_response})

        return ai_response, conversation_history

    except Exception as e:
        return f"Error: {str(e)}", conversation_history


if __name__ == "__main__":
    pass
