class CodexAccMgrError(Exception):
    """Base application error."""


class AliasAlreadyExistsError(CodexAccMgrError):
    pass


class AuthStateNotFoundError(CodexAccMgrError):
    pass


class AuthStateInvalidError(CodexAccMgrError):
    pass


class AccountNotFoundError(CodexAccMgrError):
    pass


class OptionalDependencyError(CodexAccMgrError):
    pass
