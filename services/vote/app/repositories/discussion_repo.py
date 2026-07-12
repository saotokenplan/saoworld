import uuid
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.domain.models import VoteDiscussion, VoteDiscussionReply, VoteDiscussionLike


class DiscussionSortBy:
    TIME = "time"
    HOT = "hot"


class DiscussionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_discussions(
        self,
        vote_cycle_id: uuid.UUID,
        sort_by: str = DiscussionSortBy.TIME,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[VoteDiscussion], int]:
        count_stmt = select(sa_func.count(VoteDiscussion.discussion_id)).where(
            VoteDiscussion.vote_cycle_id == vote_cycle_id,
            VoteDiscussion.status == "active",
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[VoteDiscussion]] = select(VoteDiscussion).where(
            VoteDiscussion.vote_cycle_id == vote_cycle_id,
            VoteDiscussion.status == "active",
        )

        if sort_by == DiscussionSortBy.HOT:
            stmt = stmt.order_by(VoteDiscussion.like_count.desc(), VoteDiscussion.created_at.desc())
        else:
            stmt = stmt.order_by(VoteDiscussion.created_at.desc())

        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        discussions = result.scalars().all()
        return discussions, total

    async def get_discussion(self, discussion_id: uuid.UUID) -> VoteDiscussion | None:
        stmt: Select[tuple[VoteDiscussion]] = select(VoteDiscussion).where(
            VoteDiscussion.discussion_id == discussion_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_discussion(
        self,
        vote_cycle_id: uuid.UUID,
        player_id: uuid.UUID,
        content: str,
    ) -> VoteDiscussion:
        discussion = VoteDiscussion(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            content=content,
            status="active",
        )
        self.db.add(discussion)
        await self.db.flush()
        return discussion

    async def like_discussion(
        self,
        discussion_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> bool:
        like = VoteDiscussionLike(
            player_id=player_id,
            discussion_id=discussion_id,
            reply_id=None,
        )
        self.db.add(like)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            return False

        discussion = await self.get_discussion(discussion_id)
        if discussion:
            discussion.like_count += 1
            await self.db.flush()
        return True

    async def unlike_discussion(
        self,
        discussion_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> bool:
        stmt = select(VoteDiscussionLike).where(
            VoteDiscussionLike.player_id == player_id,
            VoteDiscussionLike.discussion_id == discussion_id,
        )
        result = await self.db.execute(stmt)
        like = result.scalar_one_or_none()
        if not like:
            return False

        await self.db.delete(like)

        discussion = await self.get_discussion(discussion_id)
        if discussion and discussion.like_count > 0:
            discussion.like_count -= 1

        await self.db.flush()
        return True

    async def list_replies(
        self,
        discussion_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[VoteDiscussionReply], int]:
        count_stmt = select(sa_func.count(VoteDiscussionReply.reply_id)).where(
            VoteDiscussionReply.discussion_id == discussion_id,
            VoteDiscussionReply.status == "active",
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[VoteDiscussionReply]] = select(VoteDiscussionReply).where(
            VoteDiscussionReply.discussion_id == discussion_id,
            VoteDiscussionReply.status == "active",
        ).order_by(VoteDiscussionReply.created_at.asc()).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        replies = result.scalars().all()
        return replies, total

    async def get_reply(self, reply_id: uuid.UUID) -> VoteDiscussionReply | None:
        stmt: Select[tuple[VoteDiscussionReply]] = select(VoteDiscussionReply).where(
            VoteDiscussionReply.reply_id == reply_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_reply(
        self,
        discussion_id: uuid.UUID,
        player_id: uuid.UUID,
        content: str,
    ) -> VoteDiscussionReply:
        reply = VoteDiscussionReply(
            discussion_id=discussion_id,
            player_id=player_id,
            content=content,
            status="active",
        )
        self.db.add(reply)

        discussion = await self.get_discussion(discussion_id)
        if discussion:
            discussion.reply_count += 1

        await self.db.flush()
        return reply

    async def like_reply(
        self,
        reply_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> bool:
        like = VoteDiscussionLike(
            player_id=player_id,
            discussion_id=None,
            reply_id=reply_id,
        )
        self.db.add(like)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            return False

        reply = await self.get_reply(reply_id)
        if reply:
            reply.like_count += 1
            await self.db.flush()
        return True

    async def unlike_reply(
        self,
        reply_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> bool:
        stmt = select(VoteDiscussionLike).where(
            VoteDiscussionLike.player_id == player_id,
            VoteDiscussionLike.reply_id == reply_id,
        )
        result = await self.db.execute(stmt)
        like = result.scalar_one_or_none()
        if not like:
            return False

        await self.db.delete(like)

        reply = await self.get_reply(reply_id)
        if reply and reply.like_count > 0:
            reply.like_count -= 1

        await self.db.flush()
        return True

    async def has_liked_discussion(
        self,
        player_id: uuid.UUID,
        discussion_id: uuid.UUID,
    ) -> bool:
        stmt = select(VoteDiscussionLike).where(
            VoteDiscussionLike.player_id == player_id,
            VoteDiscussionLike.discussion_id == discussion_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_liked_reply(
        self,
        player_id: uuid.UUID,
        reply_id: uuid.UUID,
    ) -> bool:
        stmt = select(VoteDiscussionLike).where(
            VoteDiscussionLike.player_id == player_id,
            VoteDiscussionLike.reply_id == reply_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_discussion(self, discussion_id: uuid.UUID) -> VoteDiscussion | None:
        discussion = await self.get_discussion(discussion_id)
        if not discussion:
            return None
        discussion.status = "deleted"
        await self.db.flush()
        await self.db.refresh(discussion)
        return discussion

    async def delete_reply(self, reply_id: uuid.UUID) -> VoteDiscussionReply | None:
        reply = await self.get_reply(reply_id)
        if not reply:
            return None
        reply.status = "deleted"
        await self.db.flush()

        discussion = await self.get_discussion(reply.discussion_id)
        if discussion and discussion.reply_count > 0:
            discussion.reply_count -= 1
            await self.db.flush()

        await self.db.refresh(reply)
        return reply
