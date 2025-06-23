from nicegui import ui
import requests
import json
from datetime import datetime
from uuid import uuid4
import asyncio

messages = []

@ui.refreshable
def chat_messages(own_id: str):
    """Present and store the chat messages.
    """
    if messages:
        for user_id, text, stamp in messages:
            is_sent_by_user = (user_id == own_id)

            ui.chat_message(
                text=text,
                stamp=stamp,
                sent=is_sent_by_user
            ).classes(
                'rounded-2xl p-3 max-w-[80%]' +
                ('bg-gray-50 text-right self-end' if is_sent_by_user else 'bg-gray-50 self-start')
            )
    else:
        ui.label('How can I help you today?').classes('mx-auto my-36')
    
    # auto scroll to the bottom
    ui.html('<div id="chat-bottom"></div>')
    ui.run_javascript('document.getElementById("chat-bottom")?.scrollIntoView({ behavior: "smooth" });')


@ui.page('/')
async def main():
    ######################################################
    user_id = str(uuid4())

    # === Header ===
    with ui.row().classes('w-full h-16 px-4 shadow items-center justify-between bg-white'):
        ui.label('A Very Nice GUI').classes('text-xl font-bold')

        time_label = ui.label().classes('text-sm text-gray-500')

        async def update_time():
            while True:
                time_label.text = datetime.now().strftime('%Y-%m-%d %H:%M')
                await asyncio.sleep(1)

        asyncio.create_task(update_time())


    # === Main area ===
    with ui.row().classes('w-full h-full'):
        # Left side: currently blank
        with ui.column().classes('flex-grow p-6'):
            info = """
            Left Side:  
            - currently blank due to the very bad design skills of the author.
            """
            ui.markdown(info).classes('text-lg text-gray-600')

        # === Right side: chat area with LLM ===
        with ui.column().classes('w-[25%] min-w-[320px] max-w-[400px] h-[calc(100vh-4rem)] bg-gray-50 p-4 border-l gap-2'):
            
            # header
            ui.label('Chat with Ollama - Demo').classes('text-lg font-semibold')

            # chatting area
            with ui.column().classes('flex-grow overflow-y-auto gap-2 scroll-smooth'):
                chat_messages(user_id)

            # input area
            with ui.row().classes('items-center border-t pt-2'):
                user_input = ui.input(placeholder='Say something...') \
                    .on('keydown.enter', lambda _: send()) \
                    .props('rounded outlined input-class=mx-3').classes('flex-grow')
                ui.button('Send', on_click=lambda: send()).classes('ml-2')

    ######################################################
    # === send function ===
    def send():
        """Handle the `sending` message event
        """
        prompt = user_input.value
        if not prompt.strip():
            return

        stamp = datetime.now().strftime('%X')
        messages.append((user_id, prompt, stamp))
        chat_messages.refresh()
        user_input.value = ''

        # placeholder for llm reply
        placeholder_stamp = datetime.now().strftime('%X')
        placeholder = ('ollama', '', placeholder_stamp)
        messages.append(('ollama', '', placeholder_stamp))
        chat_messages.refresh()
        placeholder_index = len(messages) - 1

        asyncio.create_task(stream_response(prompt, placeholder_index))

    # === stream response ===
    async def stream_response(prompt: str, placeholder_index: int):
        """Interaction with Ollama through the API to generate response.
        """
        reply = ""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )

            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    token = data.get("response", "")
                    reply += token

                    messages[placeholder_index] = (
                        messages[placeholder_index][0],
                        reply,
                        messages[placeholder_index][2],
                    )
                    chat_messages.refresh()
                    await asyncio.sleep(0)

        except Exception as e:
            messages[placeholder_index] = (
                messages[placeholder_index][0],
                f"[ERROR] {str(e)}",
                messages[placeholder_index][2],
            )
            chat_messages.refresh()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
