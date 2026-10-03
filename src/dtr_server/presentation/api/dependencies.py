from functools import lru_cache

from dtr_server.application.build_smart_configuration import BuildSmartConfiguration
from dtr_server.application.exchange_backend_services_token import ExchangeBackendServicesToken
from dtr_server.application.get_capability_statement import GetCapabilityStatement
from dtr_server.config import Settings, get_settings
from dtr_server.infrastructure.auth.access_token_service import AccessTokenService
from dtr_server.infrastructure.auth.client_assertion_validator import ClientAssertionValidator
from dtr_server.infrastructure.auth.jwks_resolver import JwksResolver
from dtr_server.infrastructure.fhir.capability_statement_builder import CapabilityStatementBuilder


@lru_cache
def get_capability_statement_use_case() -> GetCapabilityStatement:
    return GetCapabilityStatement(CapabilityStatementBuilder())


def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_smart_configuration_builder() -> BuildSmartConfiguration:
    return BuildSmartConfiguration(get_settings())


@lru_cache
def get_token_exchange_use_case() -> ExchangeBackendServicesToken:
    settings = get_settings()
    jwks_resolver = JwksResolver(settings)
    validator = ClientAssertionValidator(
        jwks_resolver,
        allow_unverified_signature=settings.smart_allow_unverified_client_assertion,
        accepted_audiences=settings.smart_extra_audience_list,
    )
    issuer = AccessTokenService(settings)
    return ExchangeBackendServicesToken(settings, validator, issuer)
