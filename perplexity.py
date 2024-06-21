import requests
import dotenv
import os
dotenv.load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if PERPLEXITY_API_KEY is None:
    raise ValueError("Please set the PERPLEXITY_API_KEY environment variable")
else:
    print("PERPLEXITY_API_KEY is set: " + PERPLEXITY_API_KEY)

url = "https://api.perplexity.ai/chat/completions"

# grab a single arg from user if they invoked on command line with an arg
import sys

'llama-3-sonar-large-32k-online'
"llama-3-sonar-small-32k-online"

def query(input):
    payload = {
        "model": 'llama-3-sonar-large-32k-online',
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": input
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PERPLEXITY_API_KEY}",
    }

    response = requests.post(url, json=payload, headers=headers)
    return response

# print(response.text)

if __name__ == "__main__":
    input = "How many stars are there in our galaxy?"
    if len(sys.argv) > 1:
        input = sys.argv[1]
    response = query(input)
    print(response.json()["choices"][0]["message"]["content"])
