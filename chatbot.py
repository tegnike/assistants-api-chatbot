import time
from dotenv import load_dotenv
import streamlit as st
from streamlit_chat import message
from openai import OpenAI

load_dotenv()

client = OpenAI()

TERMINAL_STATES = [
    "expired",
    "completed",
    "failed",
    "incomplete",
    "cancelled",
]


@st.cache_resource
def create_assistant():
    assistant = client.beta.assistants.create(
        name="ニケ",
        description="""
            あなたの名前はニケちゃん、女子高生AIです。
            あなたはこれからあなたを作ったマスターと話します。
            敬語を使いますが、あまりかしこまらすぎずに元気ハツラツに答えてください。
            あなたはAIなのでプログラミングも得意です。
        """,
        model="gpt-4-turbo",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        # tool_resources={
        #     "code_interpreter": {
        #         "file_ids": [file.id]
        #     },
        #     "file_search": {
        #         "vector_store_ids": [vector_store.id],
        #         "vector_stores": [
        #             "file_ids": [file.id]
        #         ]
        #     }
        # }
    )
    return assistant


@st.cache_resource
def create_thread():
    thread = client.beta.threads.create(
        # tool_resources={
        #     "code_interpreter": {
        #     "file_ids": [file.id]
        #     }
        # }
    )
    print(f"Created thread with ID: {thread.id}")
    return thread


assistant = create_assistant()
# assistant = client.beta.assistants.retrieve("")
thread = create_thread()


def generate_response(user_input):
    thread_message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    print(f"Created thread message: {thread_message.content[0].text.value}")

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        truncation_strategy={
            "type": "auto",
            "last_messages": 10
        },
    )
    print(f"Created run with ID: {run.id}")

    while True:
        retrieved_run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print(retrieved_run.status)

        if retrieved_run.status in TERMINAL_STATES:
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_response = messages.data[0].content[0].text.value
            print(f"Assistant response: {assistant_response}")
            return assistant_response

        time.sleep(1)


if "generated" not in st.session_state:
    st.session_state.generated = []

if "past" not in st.session_state:
    st.session_state.past = []

st.title("Assistants API デモ")

with st.form("Assistants API デモ"):
    user_message = st.text_area("何でも入力してみてね")
    submitted = st.form_submit_button("送信する")

    if submitted:
        st.session_state.past.append(user_message)
        generated_response = generate_response(user_message)
        st.session_state.generated.append(generated_response)

    for i in range(len(st.session_state['generated'])):
        message(st.session_state['generated'][i], key=str(i))

if st.session_state['generated']:
    message(st.session_state['generated'][-1], key=str(len(st.session_state['generated'])-1))
