from django.db import models
from django.contrib.auth.models import User
from channels.models import Channel
from django.utils.timezone import now

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    certificate_id = models.CharField(max_length=20, unique=True)
    issued_on = models.DateTimeField(default=now)
    pdf = models.FileField(upload_to='certificates/') 

    def __str__(self):
        return f"{self.user.username} - {self.channel.name}"
