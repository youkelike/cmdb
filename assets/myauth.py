from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,AbstractBaseUser
)
import django

class UserManager(BaseUserManager):
    #创建普通用户
    def create_user(self,email,name,password=None):
        if not email:
            raise ValueError('Users need an Email address!')

        user = self.model(
            email = self.normalize_email(email),
            name = name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    #创建超级用户
    def create_superuser(self,email,name,password):
        '''
        命令行创建管理员是调用了这个方法
        '''
        user = self.create_user(email,name=name,password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user

class UserProfile(AbstractBaseUser):
    email = models.EmailField(max_length=255,unique=True,verbose_name='邮箱')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    name = models.CharField(u'姓名',max_length=32)
    token = models.CharField(u'token',max_length=128,default=None,blank=True,null=True)
    department = models.CharField(u'部门',max_length=32,default=None,blank=True,null=True)
    tel = models.CharField(u'座机',max_length=32,default=None,blank=True,null=True)
    mobile = models.CharField(u'手机',max_length=11,default=None,blank=True,null=True)
    memo = models.TextField(u'备注',default=None,blank=True,null=True)
    date_joined = models.DateTimeField(auto_now_add=True,blank=True)
    valid_begin_time = models.DateTimeField(default=django.utils.timezone.now)
    valid_end_time = models.DateTimeField(blank=True,null=True)
    #用户登录的用户名字段
    USERNAME_FIELD = 'email'
    #新用户必填字段列表
    REQUIRED_FIELDS = ['name']
    #必须重写的方法
    def get_full_name(self):
        return self.email
    def get_short_name(self):
        return self.email
    def __str__(self):
        return self.email
    def has_perm(self,perm,obj=None):
        return True
    def has_perms(self,perm,obj=None):
        return True
    def has_module_perms(self,app_label):
        return True
    @property
    def is_staff(self):
        return self.is_admin

    class Meta:
        verbose_name = u'用户信息'
        verbose_name_plural = u'用户信息'

    #模型类都有这个属性
    objects = UserManager()