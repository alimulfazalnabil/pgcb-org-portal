from pydantic import BaseModel, Field

class BroadcastNotification(BaseModel):
    title_bn: str = Field(min_length=2, max_length=300)
    body_bn: str = Field(min_length=2, max_length=4000)
    notification_type: str = Field(default='GENERAL', max_length=50)
    role: str | None = None
    channel: str = Field(default='IN_APP', pattern=r'^(IN_APP|EMAIL|SMS|ALL)$')
