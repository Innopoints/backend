"""A helper function that returns a timezone-aware datetime object for
the current moment in time."""

from datetime import datetime, timezone
from functools import partial


tz_aware_now = partial(datetime.now, tz=timezone.utc)
unix_epoch = datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc)
