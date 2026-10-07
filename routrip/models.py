from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id=models.AutoField(primary_key=True,
                        bd_column='ID')
    
    username=models.CharField(max_length=30,
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

class Log(models.Model):
    id=models.AutoField(primary_key=True,
                        bd_column='ID')
    
    user=models.ForeignKey('User',
                            on_delete=models.CASCADE,
                            bd_column='USER_ID',
                            related_name='logs')
    
    start_spot=models.ForeignKey('Spot',  # Assuming you have a Spot model
                                    on_delete=models.PROTECT,
                                    bd_column='START_SPOT_ID',
                                    related_name='start_logs')
    
    thumbnail_card=models.ForeignKey('LogCard',
                                on_delete=models.SET_NULL,
                                bd_column='THUMBNAIL_CARD_ID',
                                related_name='thumbnail_logs',
                                null=True,
                                blank=True)
    
    title=models.CharField(max_length=50,
                            bd_column='TITLE')
    
    posted_at=models.DateTimeField(auto_now_add=True,
                                bd_column='POSTED_AT')
    
    trip_start_date=models.DateField(bd_column='TRIP_START_DATE')
    
    trip_end_date=models.DateField(bd_column='TRIP_END_DATE')
    
    updated_at=models.DateTimeField(auto_now=True,
                                bd_column='UPDATED_AT')
    class Meta:
        db_table='LOG'
        
    def __str__(self):
        return self.title