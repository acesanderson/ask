"""
Only get 100 free searches a month.
"""

from serpapi import GoogleSearch
import dotenv
import os
import sys
import json
dotenv.load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

if SERP_API_KEY is None:
    raise ValueError("Please set the SERP_API_KEY environment variable")
else:
    print("SERP_API_KEY is set: " + SERP_API_KEY)

def Search(search_term):
    params = {
      "engine": "google",
      "q": search_term,
      "api_key": SERP_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results["organic_results"]
    return organic_results

"""
Example response

{
    "displayed_link": "https://en.wikipedia.org \u203a wiki \u203a President_of_Namibia",
    "favicon": "https://serpapi.com/searches/666797acfdca3edd38ac5982/images/cc16e88cb5486be965eba7238f5661318f770642c4f2ea6904fe5f80d82d1708.png",
    "link": "https://en.wikipedia.org/wiki/President_of_Namibia",
    "position": 1,
    "redirect_link": "https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://en.wikipedia.org/wiki/President_of_Namibia&ved=2ahUKEwijwq2Ro9KGAxUwRzABHbEeBXUQFnoECBcQAQ",
    "snippet": "President of Namibia ; Incumbent Nangolo Mbumba since 4 February 2024 ; Incumbent Nangolo Mbumba since 4 February 2024 \u00b7 His Excellency \u00b7 Head of state \u00b7 Head of ...",
    "snippet_highlighted_words": [
        "Incumbent Nangolo Mbumba"
    ],
    "source": "Wikipedia",
    "title": "President of Namibia"
}

"""

headlines = """
Chatbots aren't becoming sentient
Mirages: On Anthropomorphism in Dialogue Systems
Searching for Sentience
Human Cognitive Biases in Generative AI
ELIZA Effect
In Search of Dark Patterns in Chatbots
Impact of Voice Fidelitry on Decision Making
Dark Patterns of Cuteness: Popular Learning App Design
Tesla Faked Self Driving Demo
Google's best Gemini demo was faked
Google's AI Search Errors cause a Furor Online
Amazon Fresh kills "Just Walk Out"
"AI Washing"
Rabbit R1 is just an android app
OpenAI has a toxic culture of lying
""".strip().split("\n")

d = {}
for headline in headlines:
    print("Searching for:", headline)
    r = Search(headline)
    link=r[0]['link']
    d[headline] = link


if __name__ == "__main__":
    search_term = "What is the capital of France?"
    if len(sys.argv) > 1:
        search_term = sys.argv[1]
    results = Search(search_term)
    print(json.dumps(results, indent=4))

"""