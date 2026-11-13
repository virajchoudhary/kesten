import json

from django.utils import timezone

from .ingestion import prepare_csv_intake
from .services import DatasetUnavailable


def verify_intake(receipt, *, owner):
    if not owner.is_active or receipt.dataset.owner_id != owner.pk:
        raise DatasetUnavailable("The intake receipt is unavailable.")
    metadata = json.loads(json.dumps(receipt.dataset.payload, allow_nan=False))
    metadata.pop("observations", None)
    try:
        prepared = prepare_csv_intake(
            csv_bytes=bytes(receipt.csv_content),
            metadata=metadata,
            source_record=receipt.evidence["source"],
            terms_bytes=bytes(receipt.terms_content),
            availability_bytes=bytes(receipt.availability_content),
            now=timezone.now(),
        )
        matches = (
            prepared.dataset.version == receipt.dataset.version
            and prepared.version == receipt.version
            and json.loads(prepared.receipt_json) == receipt.evidence
        )
    except (ValueError, KeyError, TypeError) as error:
        raise DatasetUnavailable("The archived intake evidence failed verification.") from error
    if not matches:
        raise DatasetUnavailable("The archived intake evidence failed verification.")
    return {
        "receipt_id": str(receipt.id), "receipt_version": receipt.version,
        "dataset_id": str(receipt.dataset_id), "dataset_version": receipt.dataset.version,
        "match": True, "independently_verified_source": False,
        "data_kind": prepared.dataset.data_kind,
    }
