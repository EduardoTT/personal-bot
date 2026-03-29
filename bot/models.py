from django.db import models
from pydantic import BaseModel, ConfigDict


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Record(models.Model):
    text = models.TextField()
    tags = models.ManyToManyField(Tag)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class Inteligence(models.Model):
    content = models.JSONField()
    instructions = models.TextField()


class InteligenceDeserializer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: dict
    instructions: str
