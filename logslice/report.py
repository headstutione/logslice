"""Report rendering for aggregation results."""
from typing import List
from logslice.aggregator import AggregationResult


class ReportRenderer:
    """Renders AggregationResult to human-readable text."""

    def render_text(self, result: AggregationResult) -> str:
        lines: List[str] = []
        lines.append(f"Total entries: {result.total}")

        if result.groups:
            top_n = result.config.top_n
            items = result.top(top_n) if top_n else sorted(
                result.groups.items(), key=lambda x: x[1], reverse=True
            )
            lines.append(f"\nBreakdown by '{result.config.group_by}':")
            max_key_len = max((len(k) for k, _ in items), default=0)
            for key, count in items:
                bar = "#" * min(count, 40)
                lines.append(f"  {key:<{max_key_len}}  {count:>6}  {bar}")

        return "\n".join(lines)

    def render_csv(self, result: AggregationResult) -> str:
        lines: List[str] = []
        group_by = result.config.group_by or "(none)"
        lines.append(f"{group_by},count")
        if result.groups:
            for key, count in sorted(result.groups.items(), key=lambda x: x[1], reverse=True):
                safe_key = key.replace('"', '""')
                lines.append(f'"{safe_key}",{count}')
        else:
            lines.append(f'"(all)",{result.total}')
        return "\n".join(lines)
