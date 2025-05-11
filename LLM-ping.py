from openai import OpenAI

API_KEY = "sk-DCexuFsJNJS1A7DpAa8a29800e2e4488A2A016F6D6B34f99" # proxy
BASE_URL = "https://api.132999.xyz/v1"
MODELS = {
    "1": "deepseek-v3",
    "2": "claude-3-5-sonnet-all",
    "3": "gpt-3.5-turbo",
    "4": "gpt-4",
    "5": "gpt-4-32k",
    "6": "gpt-4-turbo",
    "7": "o1",
    "8": "o1-mini",
    "9": "gemini-pro"
}
MODEL = MODELS["1"]

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "你好，请问你叫什么？",
        }
    ],
    model=MODEL,
)
print(chat_completion.choices[0].message.content)