from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator

class User(AbstractUser):
    username=models.CharField(max_length=30,
                            unique=True,
                            db_column='LOGIN_ID',
                            verbose_name='ログインID',
                            validators=[ASCIIUsernameValidator()])
    
    password=models.CharField(max_length=128,
                            db_column='PASSWORD',
                            verbose_name='パスワード')
    
    display_name=models.CharField(max_length=10,
                            db_column='DISPLAY_NAME',
                            verbose_name='ユーザーネーム')
    
    is_public=models.BooleanField(default=True,
                                db_column='IS_PUBLIC',
                                verbose_name='公開設定')
    
    class Meta:
        db_table='USERS'
        
    def __str__(self):
        return self.display_name

class Log(models.Model):
    user=models.ForeignKey('User',
                            on_delete=models.CASCADE,
                            db_column='USER_ID',
                            related_name='logs',
                            verbose_name='投稿者')
    
    start_spot=models.ForeignKey('Spot',
                                    on_delete=models.PROTECT,
                                    db_column='START_SPOT_ID',
                                    related_name='start_logs',
                                    verbose_name='出発スポット')
    
    thumbnail_card=models.ForeignKey('Logcard', 
                                on_delete=models.SET_NULL,
                                db_column='THUMBNAIL_CARD_ID',
                                related_name='thumbnail_logs',
                                null=True,
                                blank=True,
                                verbose_name='サムネイルカード')
    
    title=models.CharField(max_length=50,
                            db_column='TITLE',
                            verbose_name='タイトル')
    
    posted_at=models.DateTimeField(auto_now_add=True,
                                db_column='POSTED_AT',
                                verbose_name='投稿日時')
    
    trip_start_date=models.DateField(db_column='TRIP_START_DATE',
                                    verbose_name='旅行開始日')
    
    trip_end_date=models.DateField(db_column='TRIP_END_DATE',
                                  verbose_name='旅行終了日')
    
    updated_at=models.DateTimeField(auto_now=True,
                                db_column='UPDATED_AT',
                                verbose_name='更新日時')
    
    tags=models.ManyToManyField('tag',
                                blank=True,
                                related_name='logs',
                                verbose_name='タグ')
    class Meta:
        db_table='LOG'
        
    def __str__(self):
        return self.title

class Spot(models.Model):
        registered_user=models.ForeignKey('User',
                                        on_delete=models.PROTECT,
                                        db_column='REGISTERED_USER_ID',
                                        related_name='registered_spots',
                                        verbose_name='登録者')
        
        name=models.CharField(max_length=30,
                            db_column='NAME',
                            verbose_name='スポット名')
        
        latitude=models.FloatField(db_column='LATITUDE',
                                verbose_name='緯度')
        
        longitude=models.FloatField(db_column='LONGITUDE',
                                verbose_name='経度')
        
        class Meta:
            db_table='SPOT'
            
        def __str__(self):
            return self.name

class Logcard(models.Model):
    log=models.ForeignKey('Log',
                            on_delete=models.CASCADE,
                            db_column='LOG_ID',
                            related_name='cards',
                            verbose_name='ログ')
    
    spot=models.ForeignKey('Spot',
                            on_delete=models.PROTECT,
                            db_column='SPOT_ID',
                            related_name='log_cards',
                            verbose_name='スポット')
    
    image_path=models.ImageField(
                            upload_to='photos/',
                            max_length=255,
                            null=True,
                            blank=True,
                            db_column='IMAGE_PATH',
                            verbose_name='画像')
    
    taken_at=models.DateTimeField(null=True,
                                blank=True,
                                db_column='TAKEN_AT',
                                verbose_name='撮影日時')
    
    latitude=models.FloatField(null=True,
                            blank=True,
                            db_column='LATITUDE',
                            verbose_name='緯度')
    
    longitude=models.FloatField(null=True,
                            blank=True,
                            db_column='LONGITUDE',
                            verbose_name='経度')
    
    comment=models.TextField(db_column='COMMENT',
                            verbose_name='コメント')
    
    display_order=models.IntegerField(db_column='DISPLAY_ORDER',
                                    verbose_name='表示順番号')
    
    class Meta:
        db_table='LOGCARD'
        
    def __str__(self):
        return f"Logcard {self.id}"
    
class Section(models.Model):
    log=models.ForeignKey('Log',
                            on_delete=models.CASCADE,
                            db_column='LOG_ID',
                            related_name='sections',
                            verbose_name='ログ')
    
    from_spot=models.ForeignKey('Spot',
                                    on_delete=models.PROTECT,
                                    db_column='START_SPOT_ID',
                                    related_name='departing_sections',
                                    verbose_name='出発スポット')
    
    to_spot=models.ForeignKey('Spot',
                                    on_delete=models.PROTECT,
                                    db_column='TO_SPOT_ID',
                                    related_name='arriving_sections',
                                    verbose_name='到着スポット')
    
    section_order=models.IntegerField(db_column='SECTION_ORDER',
                                    verbose_name='区間順序')
    
    transport=models.CharField(max_length=10,
                            db_column='TRANSPORT',
                            verbose_name='移動手段')
    
    duration=models.IntegerField(null=True,
                                blank=True,
                                db_column='DURATION_MIN',
                                verbose_name='所要時間（分）')
    class Meta:
        db_table='SEGMENT'
        
    def __str__(self):
        return f"Section {self.id}"

class Tag(models.Model):
    name=models.CharField(max_length=30,
                        unique=True,
                        db_column='NAME',
                        verbose_name='タグ名')
    
    class Meta:
        db_table='TAG'
        
    def __str__(self):
        return self.name
    
    