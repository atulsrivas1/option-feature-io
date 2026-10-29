"""Option-native I/O, independent of any equity transport/schema."""

from .adapter import snapshot_from_synthetic_mapping
from .errors import (PublicationConflict, StorageIntegrityError,
                     StorageSchemaError, WireFormatError)
from .publication import CommitReceipt, Publication, ResultSink
from .sink import DuckDBSink, validate_publication
from .wire import (decode_request, decode_results, decode_snapshot,
                   encode_request, encode_results, encode_snapshot)

__version__ = "0.2.0a1"
__all__ = [
    "snapshot_from_synthetic_mapping", "PublicationConflict", "StorageIntegrityError",
    "StorageSchemaError", "WireFormatError", "CommitReceipt", "Publication",
    "ResultSink", "DuckDBSink", "validate_publication", "decode_request",
    "decode_results", "decode_snapshot", "encode_request", "encode_results",
    "encode_snapshot",
]
