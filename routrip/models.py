from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id=models.AutoField(primary_key=True,
                        db_column='ID')
    
    username=models.CharField(max_length=30,
                            unique=True,
                            db_column='LOGIN_ID')
    
    password=models.CharField(max_length=50,
                            db_column='PASSWORD')
    
    display_name=models.CharField(max_length=10,
                            db_column='DISPLAY_NAME')
    
    is_public=models.BooleanField(default=True,
                                db_column='IS_PUBLIC')
    
    class Meta:
        db_table='USERS'
        
    def __str__(self):
        return self.display_name

class Log(models.Model):
    id=models.AutoField(primary_key=True,
                        db_column='ID')
    
    user=models.ForeignKey('User',
                            on_delete=models.CASCADE,
                            db_column='USER_ID',
                            related_name='logs')
    
    start_spot=models.ForeignKey('Spot',  # Assuming you have a Spot model
                                    on_delete=models.PROTECT,
                                    db_column='START_SPOT_ID',
                                    related_name='start_logs')
    
    thumbnail_card=models.ForeignKey('LogCard', 
                                on_delete=models.SET_NULL,
                                db_column='THUMBNAIL_CARD_ID',
                                related_name='thumbnail_logs',
                                null=True,
                                blank=True)
    
    title=models.CharField(max_length=50,
                            db_column='TITLE')
    
    posted_at=models.DateTimeField(auto_now_add=True,
                                db_column='POSTED_AT')
    
    trip_start_date=models.DateField(db_column='TRIP_START_DATE')
    
    trip_end_date=models.DateField(db_column='TRIP_END_DATE')
    
    updated_at=models.DateTimeField(auto_now=True,
                                db_column='UPDATED_AT')
    class Meta:
        db_table='LOG'
        
    def __str__(self):
        return self.title

class Spot(models.Model):
        id=models.AutoField(primary_key=True,
                            db_column='ID')
        
        registered_user=models.ForeignKey('User',
                                        on_delete=models.PROTECT,
                                        db_column='REGISTERED_USER_ID',
                                        related_name='registered_spots')
        
        name=models.CharField(max_length=30,
                            db_column='NAME')
        
        latitude=models.FloatField(db_column='LATITUDE')
        
        longitude=models.FloatField(db_column='LONGITUDE')
        
        class Meta:
            db_table='SPOT'
            
        def __str__(self):
            return self.name

    