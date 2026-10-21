"""Transport and storage failures never imply successful publication."""


class WireFormatError(ValueError):
    """The envelope is malformed or has an unverified digest."""


class StorageSchemaError(ValueError):
    """The destination is not the exact native option schema."""


class StorageIntegrityError(ValueError):
    """Committed content failed full typed reconstruction or digest checks."""


class PublicationConflict(ValueError):
    """An existing run key names different immutable content."""
