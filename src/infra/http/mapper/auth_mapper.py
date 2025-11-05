from src.domain.entities.auth import AuthTokenEntity
from src.infra.http.dto.auth_dto import TokenResponseDTO


class AuthMapper:
    @staticmethod
    def entity_to_token_response_dto(entity: AuthTokenEntity) -> TokenResponseDTO:
        return TokenResponseDTO(
            access_token=entity.access_token,
            refresh_token=entity.refresh_token,
            expires_in=entity.expires_in,
            refresh_expires_in=entity.refresh_expires_in,
            token_type=entity.token_type,
        )
