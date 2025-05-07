import discord
import asyncio

from src.routines.qa_pipeline import run_qa_pipeline


class DiscordQABot(discord.Client):
    def __init__(
            self,
            agents,
            embedding_model,
            vector_storage,
            global_prompt=""
    ):
        super().__init__(intents=discord.Intents.default())
        self.agents = agents
        self.embedding_model = embedding_model
        self.vector_storage = vector_storage
        self.global_prompt = global_prompt

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Respond only when bot is mentioned
        if self.user in message.mentions:
            user_query = message.content.replace(f'<@{self.user.id}>', '').strip()
            if not user_query:
                await message.channel.send("Please ask a question after mentioning me.")
                return

            await message.channel.send("Thinking...")

            # Run the QA pipeline (in executor for non-blocking)
            loop = asyncio.get_running_loop()
            answer = await loop.run_in_executor(
                None,
                lambda: run_qa_pipeline(
                    user_query=user_query,
                    agents=self.agents,
                    embedding_model=self.embedding_model,
                    vector_storage=self.vector_storage,
                    global_prompt=self.global_prompt,
                    max_iterations=5,
                )
            )

            # Send final answer (and optionally extra info)
            await message.channel.send(f"**Answer:** {answer.final_answer}")


def discord_routine(
        agents,
        embedding_model,
        vector_storage,
        global_prompt="",
        bot_token=""
):
    """
    Starts the Discord bot for answering questions via QA pipeline.
    """
    # bot_token should be securely managed (e.g., environment variable)
    client = DiscordQABot(
        agents=agents,
        embedding_model=embedding_model,
        vector_storage=vector_storage,
        global_prompt=global_prompt
    )
    client.run(bot_token)