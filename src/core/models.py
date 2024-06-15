from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import mapped_column, Mapped

from .driver import Base


class AIRequest(Base):
    __tablename__ = "ai_request"

    id = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    token_sc_adr = mapped_column(String, nullable=False, unique=True)
    answer = mapped_column(String, default="")
    provider = mapped_column(String, default='eth')
    handled = mapped_column(Boolean, default=False)

    def to_dict(self):
        return {field.token: getattr(self, field.token) for field in self.__table__.c}
