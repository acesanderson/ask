import dotenv
import os
from groq import Groq
# set up our environment
dotenv.load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

models = ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"]


client = Groq(
    # This is the default and can be omitted
    api_key=groq_api_key,
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of low latency LLMs",
        }
    ],
    model=models[1],
)
print(chat_completion.choices[0].message.content)