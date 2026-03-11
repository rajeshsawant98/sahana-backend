#!/bin/bash

IMAGE="gcr.io/sahana-deaf0/sahana-backend"

echo "Fetching image list..."

DIGESTS=$(gcloud container images list-tags "$IMAGE" \
  --sort-by="~timestamp" \
  --format="get(digest)")

KEEP_FIRST=true

for DIGEST in $DIGESTS; do
  if $KEEP_FIRST; then
    echo "Keeping latest: $DIGEST"
    KEEP_FIRST=false
    continue
  fi
  echo "Deleting: $DIGEST"
  gcloud container images delete "$IMAGE@$DIGEST" --quiet
done

echo "Cleanup complete."
