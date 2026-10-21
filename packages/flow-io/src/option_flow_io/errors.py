"""Failures remain failures; no storage migration or overwrite fallback."""


class StorageSchemaError(RuntimeError):
    pass


class StorageIntegrityError(RuntimeError):
    pass


class PublicationConflict(RuntimeError):
    pass
