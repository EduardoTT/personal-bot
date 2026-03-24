from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Record(models.Model):
    text = models.TextField()
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.text
