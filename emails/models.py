from django.db import models
# Create your models here.


class Email(models.Model):

    from_email = models.EmailField(max_length=200)
    to_email = models.EmailField(max_length=200)
    subject = models.CharField(max_length=200)
    message = models.CharField(max_length=200)
    file = models.FileField(null=True, upload_to="files/")
    # send_time = models.DateTimeField(default=datetime.now)
    send_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=200, default="sent")
    important = models.BooleanField(max_length=10, default=False)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['-id']
