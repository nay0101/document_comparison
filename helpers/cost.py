from langfuse import Langfuse
from typing import Optional
import datetime as dt


def get_total_cost(
    chat_id: str,
    from_timestamp: Optional[dt.datetime] = None,
    to_timestamp: Optional[dt.datetime] = None,
) -> float:
    langfuse = Langfuse()

    langfuse_config = {
        "user_id": chat_id,
        "from_timestamp": from_timestamp,
        "to_timestamp": to_timestamp,
    }

    total_pages = langfuse.fetch_traces(**langfuse_config).meta.total_pages

    cost = 0
    for page_number in range(0, total_pages):
        traces = langfuse.fetch_traces(page=page_number + 1, **langfuse_config)
        for trace in traces.data:
            cost += trace.total_cost

    rounded_cost = round(cost, 6)
    return rounded_cost
