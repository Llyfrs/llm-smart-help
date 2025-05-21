from idlelib.rpc import response_queue

import discord
import asyncio
import copy
from src.vectordb.rating_storage import RatingStorage


class RatingView(discord.ui.View):
    """
    A reusable view for recording user feedback on a bot's answer.
    """
    def __init__(
        self,
        question: str,
        answer: str,
        iteration: int,
        cost: float,
        storage: RatingStorage,
        author_id: int,
        replied_message: discord.Message
    ):
        super().__init__(timeout=None)  # 1 hour

        self.question = question
        self.answer = answer
        self.iteration = iteration
        self.cost = cost
        self.storage = storage
        self.author_id = author_id
        self.replied_message = replied_message

    async def _validate_user(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the user who asked the question can rate this answer.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label='👍 Good', style=discord.ButtonStyle.success)
    async def good(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._validate_user(interaction):
            return
        await self.record_rating(1, interaction)

    @discord.ui.button(label='👎 Bad', style=discord.ButtonStyle.danger)
    async def bad(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._validate_user(interaction):
            return
        await self.record_rating(0, interaction)

    async def record_rating(self, score: int, interaction: discord.Interaction):
        try:
            self.storage.save_query(
                query_text=self.question,
                answer=self.answer,
                iteration=self.iteration,
                cost=self.cost,
                score=score
            )
        except Exception as e:
            print(f"Error saving rating: {e}")

        await interaction.response.send_message('Thanks for your feedback!', ephemeral=True)
        for child in self.children:
            child.disabled = True
        await self.replied_message.edit(content=self.replied_message.content, view=self)

class DiscordQABot(discord.Client):
    def __init__(
        self,
        qna_pipeline,
        rating_storage: RatingStorage,
        bot_token: str,
        max_questions_per_user: int = None,
        max_questions_global: int = None,
        guild_ids=None,
        channel_ids=None
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.qna_pipeline = qna_pipeline
        self.storage = rating_storage
        # Normalize guild_ids to ints
        self.guild_ids = set(map(int, guild_ids)) if guild_ids else set()
        # Normalize channel_ids to ints
        self.channel_ids = set(map(int, channel_ids)) if channel_ids else set()
        self.max_questions_per_user = max_questions_per_user
        self.user_question_counts = {}
        self.max_questions_global = max_questions_global
        self.question_count = 0

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message: discord.Message):

        if message.author == self.user:
            return
        if self.guild_ids and message.guild and message.guild.id not in self.guild_ids:
            return
        if self.channel_ids and message.channel.id not in self.channel_ids:
            return

        if self.user not in message.mentions:
            return

        if message.reference:
            return

        ## Check global question limit
        if self.max_questions_global is not None:
            if self.question_count >= self.max_questions_global:
                await message.reply(
                    f"The bot has reached the global limit of {self.max_questions_global} questions."
                )
                return
            # increment count immediately to block concurrent requests
            self.question_count += 1

        author_id = message.author.id
        # enforce per-user limit
        if self.max_questions_per_user is not None:
            count = self.user_question_counts.get(author_id, 0)
            if count >= self.max_questions_per_user:
                await message.reply(
                    f"You have reached the limit of {self.max_questions_per_user} questions."
                )
                return
            # increment count immediately to block concurrent requests
            self.user_question_counts[author_id] = count + 1

        user_query = message.content.replace(f'<@{self.user.id}>', '').strip()
        if not user_query:
            await message.reply("Please ask a question after mentioning me.")
            # decrement count if invalid query
            if self.max_questions_per_user is not None:
                self.user_question_counts[author_id] -= 1
            return

        thinking_msg = await message.reply("Thinking...")
        local_qna = copy.copy(self.qna_pipeline)
        loop = asyncio.get_running_loop()

        try:
            result = await loop.run_in_executor(
                None,
                lambda: local_qna.run(user_query)
            )
            await thinking_msg.delete()

            response_text = f"{result.final_answer}\n"

            # Split response if it's too long
            response_chunks = [
                response_text[i:i + 2000]
                for i in range(0, len(response_text), 2000)
            ]

            # Send the first chunk as a reply to the original message
            replied = await message.reply(response_chunks[0])

            # Send remaining chunks normally
            for chunk in response_chunks[1:]:
                replied = await message.channel.send(chunk)

            # Attach rating view to the **last** message sent
            view = RatingView(
                question=user_query,
                answer=result.final_answer,
                iteration=len(result.satisfactions),
                cost=result.cost,
                storage=self.storage,
                author_id=author_id,
                replied_message=replied
            )
            await replied.edit(view=view)

        except Exception as e:
            await thinking_msg.delete()
            await message.reply("Error occurred while processing your query")
            print(f"Error processing query: {e}")


def run_discord_routine(
    qna_pipeline,
    rating_storage: RatingStorage,
    bot_token: str,
    max_questions_per_user: int = None,
    max_questions_global: int = None,
    guild_ids=None,
    channel_ids=None
):
    """
    Run a discord bot that when tagged will answer users questions using the QAPipeline. Provides users with option to rate the answer.
    :param qna_pipeline:
        QAPipeline instance to be used for answering questions.
    :param rating_storage:  Storage instance to save user ratings.
    :param bot_token:
        Discord bot token for authentication.
    :param max_questions_per_user:
        Maximum number of questions a user can ask.
    :param max_questions_global:
        Maximum number of questions the bot can answer globally.
    :param guild_ids:
        List of guild IDs where the bot will be active.
    :param channel_ids:
        List of channel IDs where the bot will be active.
    :return: Keeps running until interrupted.
    """
    client = DiscordQABot(
        qna_pipeline=qna_pipeline,
        rating_storage=rating_storage,
        bot_token=bot_token,
        max_questions_per_user=max_questions_per_user,
        max_questions_global=max_questions_global,
        guild_ids=guild_ids,
        channel_ids=channel_ids
    )
    client.run(bot_token)
