"""R26 option-flow-variants1 strict JSON envelope codec (I/O layer).

Consumes the closed record inventory, canonical bytes and digests of
option_feature_contracts.variants1. Decoding applies the wire precedence
stages this layer owns: stage 1 (size, UTF-8, depth), stage 2 (JSON syntax,
UTF-8 BOM, duplicate keys), stage 3/4 (envelope identity, closed shape, scalars)
and stage 9 (canonical bytes, content digest). Semantic stages 5-8 belong to
the producer and are not performed here.
"""

from option_feature_contracts.variants1 import VariantValidationError

from .codec import decode_record, encode_record, record_sha256
from .coherence import check_results_coherence

__all__ = ["VariantValidationError", "check_results_coherence", "decode_record",
           "encode_record", "record_sha256"]
