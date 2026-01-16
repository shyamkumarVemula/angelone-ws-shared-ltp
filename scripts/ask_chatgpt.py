from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

def ask(prompt):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content

print(ask("Explain WinError 10060 in WebSocket"))
