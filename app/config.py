import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "智教星瞳 Backend"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./zhijiao.db"

    # Mock模式开关：True时返回模拟数据，False时调用真实AI服务
    USE_MOCK_DATA: bool = False

    # 九问平台（蓝心大模型）配置
    JIUWEN_API_BASE_URL: str = "https://jiuwen.vivo.com.cn/v1"
    JIUWEN_API_KEY: str = "app-A2fGstROcDyJ01yvZ87Q47IK"
    # 智能体ID（预留，当前九问API通过密钥区分Bot，可不填）
    JIUWEN_AGENT_ID_DIAGNOSIS_QUESTIONS: str = ""
    JIUWEN_AGENT_ID_DIAGNOSIS_REPORT: str = ""
    JIUWEN_AGENT_ID_RESOURCE: str = ""
    JIUWEN_AGENT_ID_ADJUSTMENT: str = ""
    JIUWEN_AGENT_ID_REPORT: str = ""
    JIUWEN_AGENT_ID_EXERCISE: str = ""

    AI_REQUEST_TIMEOUT: int = 180

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()