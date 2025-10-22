# apps/session/models.py
# please buat models gilang harus ada ini sementara
from django.db import models

class Session(models.Model):
    """
    Placeholder model untuk Session.
    Sementara ini hanya memiliki field ID dan nama saja.
    """
    session_key = models.PositiveIntegerField(primary_key=True) 
    name = models.CharField(max_length=255) 

    def __str__(self):
        return self.name
