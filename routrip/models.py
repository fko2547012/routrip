from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id=models.AutoField(primary_key=True,
                        bd_column='ID')
    
    login_id=models.CharField(max_length=30,
                            unique=True,
                            bd_column='LOGIN_ID')
    
    password=models.CharField(max_length=50,
                            bd_column='PASSWORD')
    
    display_name=models.CharField(max_length=10,
                            bd_column='DISPLAY_NAME')
    
    is_public=models.BooleanField(default=True,
                                bd_column='IS_PUBLIC')
    
    class Meta:
        db_table='USERS'
        
    def __str__(self):
        return self.display_name
