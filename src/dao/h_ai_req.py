from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
import typing

from src.core.models import AIRequest


class AIReqDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists_token_report(self, _token_sc_adr: str) -> typing.Optional[str]:
        sql = select(AIRequest).where(AIRequest.token_sc_adr == _token_sc_adr)
        data = await self.session.execute(sql)
        ai_req: AIRequest = data.scalar_one_or_none()
        if not ai_req:
            return None
        else:
            if not ai_req.handled:
                return None
            else:
                return ai_req.answer 
    
    async def stmt_exist_ai_request(self, _token_sc_adr: str) -> bool:
        sql = select(AIRequest).where(AIRequest.token_sc_adr == _token_sc_adr)
        data = await self.session.execute(sql)
        if not data.scalars().all():
            return False
        else:
            return True
        
    async def get_ai_request(self, _token_sc_adr) -> typing.Optional[AIRequest]:
        sql = select(AIRequest).where(AIRequest.token_sc_adr == _token_sc_adr)
        data = await self.session.execute(sql)
        return data.scalars().one_or_none()
    
    async def stmt_add_ai_request(self, ai_request_data):
        stmt = AIRequest(**ai_request_data)
        self.session.add(stmt)
        await self.session.commit()
        return stmt.id
    
    async def stmt_update_ai_request_by_adr(self, adr, ai_request_data):
        sql = select(AIRequest).where(AIRequest.token_sc_adr == adr)
        data = await self.session.execute(sql)
        ai_req: AIRequest = data.scalars().one_or_none()
        if not ai_req:
            #@todo raise exception
            return False
        else:
            ai_req.answer = ai_request_data['answer']
            ai_req.handled = ai_request_data['handled']
            await self.session.commit()
            return True
        
    async def stmt_delete_ai_request_by_adr(self, adr):
        sql = select(AIRequest).where(AIRequest.token_sc_adr == adr)
        data = await self.session.execute(sql)
        ai_req: AIRequest = data.scalars().one_or_none()
        if not ai_req:
            #@todo raise exception
            return False
        else:
            await self.session.delete(ai_req)
            await self.session.commit()
            return True