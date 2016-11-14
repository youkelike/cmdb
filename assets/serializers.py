from assets.myauth import UserProfile
from assets import models
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        #展示指定的字段
        fields = ('url','name','email','is_admin')

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Asset
        #展示关联表的深度
        depth = 1
        # 如果要加入关联表信息(一对一反向用<关联表名>，一对一正向或者一对多正向用<关联字段名>，一对多反向用<关联表名_set>)，关联表名都小写
        # 把外键字段加入前必须先在rest_urls里注册url，否则不能正常获取关联表里面的内容，会报错
        fields = ('name','sn','server','networkdevice','business_unit','manufactory','ram_set')

class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Server
        #展示所有字段
        fields = '__all__'

class ManufactorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Manufactory
        fields = '__all__'

class RAMSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RAM
        fields = '__all__'
