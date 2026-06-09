from django.db.models import Count
from discord_clone.models import Message

duplicates = (
    Message.objects.values(
        "source",
        "target",
        "timestamp",
        "content"
    )
    .annotate(cnt=Count("id"))
    .filter(cnt__gt=1)
)

deleted = 0

for dup in duplicates:
    rows = list(
        Message.objects.filter(
            source=dup["source"],
            target=dup["target"],
            timestamp=dup["timestamp"],
            content=dup["content"]
        ).order_by("id")
    )

    for row in rows[1:]:
        row.delete()
        deleted += 1

print(f"Usunięto {deleted} duplikatów")