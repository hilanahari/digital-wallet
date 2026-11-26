class WalletError(Exception):
    pass


class AccountNotFoundError(WalletError):
    pass


class SameAccountError(WalletError):
    pass


class InsufficientFundsError(WalletError):
    pass
