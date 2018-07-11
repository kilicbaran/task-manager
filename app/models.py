from django.db import models


class Task(models.Model):
    description = models.CharField(max_length=200)
    deadline = models.DateTimeField(null=True, blank=True)
    archive_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['deadline']


class Tag(models.Model):
    text = models.CharField(max_length=20)
    tasks = models.ManyToManyField(Task)
