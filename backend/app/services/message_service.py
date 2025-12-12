import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from openai import AsyncOpenAI

from app.core.redis_client import reset_unread
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_reaction_repository import MessageReactionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.message.message_page import MessagePage
from app.schemas.message.message_read import MessageRead
from app.utils.errors.database_exception import DatabaseException
from app.utils.errors.resource_not_found import ResourceNotFoundException
from app.utils.errors.service_unavailable_exception import ServiceUnavailableException
from app.utils.errors.unauthorized_exception import UnauthorizedException
from app.utils.errors.validation_exception import ValidationException


logger = logging.getLogger(__name__)


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        user_repo: UserRepository,
        reaction_repo: MessageReactionRepository,
        openai_client: AsyncOpenAI | None = None,
        model_name: str = "gpt-4o-mini",
    ):
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.user_repo = user_repo
        self.reaction_repo = reaction_repo
        self.openai_client = openai_client
        self.model_name = model_name
        self._summary_message_cap = 100
        self._spammy_tokens = {
            "ok",
            "k",
            "kk",
            "okey",
            "lmao",
            "lol",
            "haha",
            "thx",
            "thanks",
            "👍",
        }

    async def _ensure_conversation_exists(self, conversation_id: UUID):
        conv = await self.conversation_repo.get_by_id(conversation_id)
        if not conv:
            raise ResourceNotFoundException("Conversation not found")
        return conv

    async def _ensure_member(self, conversation_id: UUID, user_id: UUID):
        conv = await self._ensure_conversation_exists(conversation_id)

        is_member = await self.conversation_repo.is_member(conversation_id, user_id)
        if not is_member:
            raise UnauthorizedException("You are not part of this conversation.")
        return conv

    def _format_transcript(self, messages) -> list[str]:
        lines: list[str] = []
        for msg in messages:
            content = (msg.content or "").strip()
            if not content:
                continue

            compact = " ".join(content.split())
            lowered = compact.lower()
            if len(compact) <= 2 or lowered in self._spammy_tokens:
                continue

            sender = getattr(msg, "sender", None)
            sender_label = (
                getattr(sender, "username", None)
                or getattr(sender, "email", None)
                or "Someone"
            )
            lines.append(f"User {sender_label}: {compact}")
        return lines

    async def send_message(
        self,
        *,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
    ):
        if not content or not content.strip():
            raise ValidationException("Message content cannot be empty")

        await self._ensure_member(conversation_id, sender_id)

        msg = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
        )

        await self.conversation_repo.increment_unread_for_others(
            conversation_id=conversation_id,
            sender_id=sender_id,
        )

        return msg

    async def mark_delivered(self, message_id: UUID):
        return await self.message_repo.mark_delivered(message_id)

    async def mark_read(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        before_message_id: Optional[UUID] = None,
    ):
        await self._ensure_member(conversation_id, user_id)
        updated = await self.message_repo.mark_messages_as_read(
            conversation_id=conversation_id,
            user_id=user_id,
            before_message_id=before_message_id,
        )

        if updated:
            await reset_unread(user_id, conversation_id)
            last_msg = updated[-1]
            await self.conversation_repo.update_last_read(
                conversation_id=conversation_id,
                user_id=user_id,
                message_id=last_msg.id,
            )

        return updated

    async def get_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
        mark_read: bool = True,
    ):
        await self._ensure_member(conversation_id, user_id)

        messages = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            before_id=before_id,
        )

        # Mark as read
        if mark_read and messages:
            last_msg = messages[-1]
            updated = await self.message_repo.mark_messages_as_read(
                conversation_id=conversation_id,
                user_id=user_id,
                before_message_id=last_msg.id,
            )

            if updated:
                # Reset unread in Redis
                await reset_unread(user_id, conversation_id)

                # Sync DB unread indexes
                await self.conversation_repo.update_last_read(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message_id=last_msg.id,
                )

        return messages

    async def get_messages_as_schema(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> List[MessageRead]:
        messages = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before_id,
        )
        counts = await self.reaction_repo.get_counts_for_messages([m.id for m in messages])
        return [
            MessageRead.model_validate(m).model_copy(update={"reactions": counts.get(m.id, {})})
            for m in messages
        ]

    # for infinite scroll UI
    async def get_message_page(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 50,
        before_id: Optional[UUID] = None,
    ) -> MessagePage:
        messages = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before_id,
        )
        counts = await self.reaction_repo.get_counts_for_messages([m.id for m in messages])

        if not messages:
            return MessagePage(
                conversation_id=conversation_id,
                messages=[],
                has_more=False,
                next_before_id=None,
            )

        # Determine if there are more messages
        oldest_msg = messages[0]

        # Try fetching one more older message
        extra = await self.message_repo.get_messages(
            conversation_id=conversation_id,
            limit=1,
            before_id=oldest_msg.id,
        )

        has_more = len(extra) > 0
        next_before_id = oldest_msg.id if has_more else None

        return MessagePage(
            conversation_id=conversation_id,
            messages=[
                MessageRead.model_validate(m).model_copy(update={"reactions": counts.get(m.id, {})})
                for m in messages
            ],
            has_more=has_more,
            next_before_id=next_before_id,
        )

    async def summarize_conversation(self, conversation_id: UUID, user_id: UUID, hours: int | None) -> str:
        if hours is not None and hours < 1:
            raise ValidationException("Hours must be at least 1")
        await self._ensure_member(conversation_id, user_id)

        if not self.openai_client:
            logger.error("OpenAI client is not configured; cannot summarize conversation %s", conversation_id)
            raise ServiceUnavailableException("Service unavailable")

        if hours is None:
            # Fetch most recent chunk
            messages = await self.message_repo.get_messages(
                conversation_id=conversation_id,
                limit=self._summary_message_cap,
            )
        else:
            threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            messages = await self.message_repo.get_messages_since(
                conversation_id=conversation_id,
                since=threshold,
                limit=self._summary_message_cap,
            )

        transcript_lines = self._format_transcript(messages)
        if not transcript_lines:
            return "Nothing significant happened."

        transcript = "\n".join(transcript_lines[-self._summary_message_cap :])

        system_prompt = (
            "You are an expert Chat Summarizer for trip planning. Extract plans, decisions, and key info from the provided transcript.\n\n"
            "RULES:\n"
            "1) Combine fragments: users may say \"hai maine\" then \"la 10\" then \"Auchan\" or \"cabana\" in separate messages. Merge them into one coherent point.\n"
            "2) Keep any references to destination/cabin, lodging links, dates/times, meeting points, routes/transport, supplies/food lists, costs, and who is going. Do NOT drop short planning fragments.\n"
            "3) Ignore only pure noise (lol, haha, random letters). Anything that sounds like planning (time, place, route, cabin, shopping list) must be kept.\n"
            "4) Output a concise bulleted list (each bullet starts with '-'). Cover: purpose/destination (e.g., cabana), lodging/link, when, where to meet, how to get there, who confirmed, what to bring/buy, and any open questions. If these items exist in the transcript, include them—do NOT omit destination/cabin details even if time/meeting exists.\n"
            "5) Detect the dominant language of the conversation (e.g., Romanian) and write the summary in that language.\n"
            "6) If multiple planning items exist, produce multiple bullets (do not collapse everything into a single meeting note)."
        )
        user_prompt = (
            f"Summarize what happened in the last {hours} hours.\n\n"
            f"Transcript:\n{transcript}"
        )

        try:
            completion = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=240,
            )
        except Exception as exc:
            logger.exception("Failed to generate summary for conversation %s", conversation_id)
            raise ServiceUnavailableException("Service unavailable") from exc

        summary = (
            completion.choices[0].message.content.strip()
            if getattr(completion, "choices", None)
            else ""
        )
        return summary or "Nothing significant happened."

    async def edit_message(self, message_id: UUID, editor_id: UUID, new_content: str):

        if new_content is None:
            raise ValidationException("New content required")

        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        if msg.sender_id != editor_id:
            raise UnauthorizedException("Only the sender can edit the message")

        await self._ensure_member(msg.conversation_id, editor_id)

        updated_msg, edit_record = await self.message_repo.edit_message(message_id, editor_id, new_content)
        if not updated_msg:
            raise DatabaseException("Failed to edit message")
        return updated_msg, edit_record

    async def delete_message(self, message_id: UUID, requester_id: UUID):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        # allow only sender to delete for now
        if msg.sender_id != requester_id:
            raise UnauthorizedException("Only the sender can delete the message")
        await self._ensure_member(msg.conversation_id, requester_id)

        deleted = await self.message_repo.delete_message(message_id)
        return deleted

    async def add_reaction(self, message_id, user_id, emoji):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        
        if not emoji or not emoji.strip():
            raise ValidationException("Emoji cannot be empty")

        await self._ensure_member(msg.conversation_id, user_id)
        reaction = await self.reaction_repo.add_reaction(message_id, user_id, emoji)
        counts = await self.reaction_repo.get_reaction_counts(message_id)

        return reaction, counts

    async def remove_reaction(self, message_id, user_id, emoji):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")
        
        if not emoji or not emoji.strip():
            raise ValidationException("Emoji cannot be empty")

        removed = await self.reaction_repo.remove_reaction(message_id, user_id, emoji)
        counts = await self.reaction_repo.get_reaction_counts(message_id)
        return removed, counts

    async def get_reactions(self, message_id, user_id):
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        await self._ensure_member(msg.conversation_id, user_id)

        reactions = await self.reaction_repo.get_reactions(message_id)
        return reactions

    async def get_reaction_users_for_emoji(self, message_id: UUID, user_id: UUID, emoji: str) -> List[str]:
        msg = await self.message_repo.get_by_id(message_id)
        if not msg:
            raise ResourceNotFoundException("Message not found")

        await self._ensure_member(msg.conversation_id, user_id)

        usernames_by_emoji = await self.reaction_repo.get_usernames_grouped_by_emoji(message_id)
        return usernames_by_emoji.get(emoji, [])
