from django.db import models

class Message(models.Model):
    source = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    content = models.TextField()

    def __str__(self):
        return f"{self.source}: {self.target}"