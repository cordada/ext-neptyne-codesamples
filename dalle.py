from openai import OpenAI


def call_dalle(prompt: str) -> str:
    client = OpenAI()
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="512x512",
        quality="standard",
        n=1,
    )
    return response.data[0].url


def dalle(subject: str, action: str, style: str) -> str:
    prompt = f"{subject} {action} in {style} style"
    return call_dalle(prompt)
