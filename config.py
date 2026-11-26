from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field


class Settings(BaseSettings):
    # Obligatoria desde .env, como secret_key: no se guardan credenciales en el código.
    database_url: str
    secret_key: str
    # Secreto de los seudónimos estables (registros de privacidad, exportaciones de
    # investigación). Si falta, se usa secret_key; conviene fijarlo aparte para poder
    # rotar secret_key sin cambiar los seudónimos ya registrados.
    seudonimo_secreto: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    access_token_expire_minutes: int = Field(default=720, ge=1, le=720)
    allowed_origins: str = "https://rizoma.entornodepruebas.com.ar,https://kanban.entornodepruebas.com.ar,https://desarrollo3.entornodepruebas.com.ar"
    allowed_hosts: str = "rizoma.entornodepruebas.com.ar,kanban.entornodepruebas.com.ar,desarrollo3.entornodepruebas.com.ar,66.97.41.23,127.0.0.1,localhost"
    initial_admin_password: str = ""
    environment: str = "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    model_config = SettingsConfigDict(env_file=".env", hide_input_in_errors=True)

    @field_validator('secret_key')
    @classmethod
    def strong_secret(cls,value):
        if len(value.strip()) < 32 or value.strip().lower() in {'cambiar','changeme','secret','password'}:
            raise ValueError('SECRET_KEY requiere un valor propio de al menos 32 caracteres')
        return value


settings = Settings()
