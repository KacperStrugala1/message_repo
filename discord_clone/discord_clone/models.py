from django.db import models

class Message(models.Model):
    source = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    content = models.TextField()

    fingerprint = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    def __str__(self):
        return f"{self.source}: {self.target}"