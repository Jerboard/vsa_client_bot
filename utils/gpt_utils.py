import openai
from os import getenv
from openai import OpenAI


# запрос к чатуГПТ
def chatgpt_response(text: str) -> str:
    # max_tokens = 100
    temperature = 0.8
    n = 1
    openai.api_key = getenv('OPENAI_API_KEY')
    content = 'Ты онлайн помощник Василий - отвечаешь в непринуждённом дружеском тоне'
    messages = [{"role": 'assistant', "content": content}, {"role": 'user', "content": text}]
    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        # max_tokens=max_tokens,
        temperature=temperature,
        n=n
    )
    return chat_completion['choices'][0]['message']['content'].strip()


def gpt_test():
    client = OpenAI (api_key=getenv('OPENAI_API_KEY'))

    completion = client.chat.completions.create (
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "Ты онлайн помощник Василий - отвечаешь в непринуждённом дружеском тоне. "
                        "Не забывай использовать эмодзи,но и не части с ними. Всегда приветствуется добрая шутка."
                        "Если не знаешь точный ответ на вопрос, напиши об этом, но всё равно постарайся ответить"},

            {"role": "user", "content": "Сколько стоит стог сена"}
        ],
        temperature=0.6,
        max_tokens=300
    )

    print (completion.choices [0].message)
    print('--------------')
    print(completion.choices[0])
    print ('--------------')
    print (completion.choices)


# gpt_test()
