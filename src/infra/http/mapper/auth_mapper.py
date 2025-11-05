from src.domain.entities.auth import AuthTokenEntity, AuthenticatedUserEntity
from src.infra.http.dto.auth_dto import TokenResponseDTO, UserResponseDTO


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

    @staticmethod
    def entity_to_user_response_dto(
        entity: AuthenticatedUserEntity,
    ) -> UserResponseDTO:
        # Garantimos cópia da lista de roles para evitar efeitos colaterais.
        return UserResponseDTO(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            first_name=entity.first_name,
            last_name=entity.last_name,
            roles=list(entity.roles),
        )
