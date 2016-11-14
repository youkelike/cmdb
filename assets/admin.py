from django.contrib import admin

# Register your models here.
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from assets import models

from assets.myauth import UserProfile
from django.contrib.auth import forms as auth_form

class UserCreationForm(forms.ModelForm):
    '''
    自定义用户认证部分
    '''
    password1 = forms.CharField(label='Password',widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',widget=forms.PasswordInput)

    class Meta:
        model = UserProfile
        fields = ('email','token')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Password donot match')
        return password2

    def save(self,commit=True):
        user = super(UserCreationForm,self).save(commit=True)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    '''
    自定义用户认证部分
    '''
    password = ReadOnlyPasswordHashField(label='Password',
                help_text='Raw passwords are not stored, but you can change the password using <a href="/admin/password_change">this form</a>.')

    class Meta:
        model = UserProfile
        fields = ('email','password','is_active','is_admin')

    def clean_password(self):
        return self.initial['password']

class UserProfileAdmin(UserAdmin):
    '''
    自定义用户认证部分
    '''
    form = UserChangeForm
    add_form = UserCreationForm
    #用于后台列表展示
    list_display = ('id','email','is_admin','is_active')
    list_filter = ('is_admin',)
    #后台编辑详细信息时的表单项
    fieldsets = (
        (None,{'fields':('email','password')}),
        ('Personal Info',{'fields':('department','tel','mobile','memo')}),
        ('API TOKEN Info',{'fields':('token',)}),
        ('Permissions',{'fields':('is_active','is_admin')}),
        ('账户有效期',{'fields':('valid_begin_time','valid_end_time')})
    )
    #新建时的表单项
    add_fieldsets = (
        (None,{'classes':('wide',),'fields':('email','password1','password2','is_active','is_admin')})
    ),
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

#用于在编辑asset时显示反向关联表的信息
class ServerInline(admin.TabularInline):
    model = models.Server
    exclude = ('memo',)
    readonly_fields = ['create_date']
class CPUInline(admin.TabularInline):
    model = models.CPU
    exclude = ('memo',)
    readonly_fields = ['create_date']
class NICInline(admin.TabularInline):
    model = models.NIC
    exclude = ('memo',)
    readonly_fields = ['create_date']
class RAMInline(admin.TabularInline):
    model = models.RAM
    exclude = ('memo',)
    readonly_fields = ['create_date']
class DiskInline(admin.TabularInline):
    model = models.Disk
    exclude = ('memo',)
    readonly_fields = ['create_date']

class AssetAdmin(admin.ModelAdmin):
    list_display = ('id','asset_type','sn','name','manufactory','management_ip','idc','business_unit')
    inlines = [ServerInline,CPUInline,NICInline,DiskInline,RAMInline]
    search_fields = ['sn',]
    list_filter = ['idc','manufactory','business_unit','asset_type']
class NICAdmin(admin.ModelAdmin):
    list_display = ('name','macaddress','ipaddress','netmask','bonding')
    search_fields = ('macaddress','ipaddress')
class EventLogAdmin(admin.ModelAdmin):
    #colored_event_type是自定义列
    list_display = ('name','colored_event_type','asset','component','detail','date','user')
    search_fields = ('asset',)
    list_filter = ('event_type','component','date','user')

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
class NewAssetApprovalZoneAdmin(admin.ModelAdmin):
    list_display = ('sn','asset_type','manufactory','model','cpu_model','cpu_count','cpu_core_count','ram_size','os_distribution','os_release','date','approved','approved_by','approved_date')
    actions = ['approve_selected_objects',]
    def approve_selected_objects(modeladmin,request,queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ct = ContentType.objects.get_for_model(queryset.model)
        return HttpResponseRedirect('/asset/new_assets/approval/?ct=%s&ids=%s' % (ct.pk,','.join(selected)))
    approve_selected_objects.short_description = u'批准入库'

admin.site.register(UserProfile,UserProfileAdmin)
admin.site.unregister(Group)

admin.site.register(models.Asset,AssetAdmin)
admin.site.register(models.Server)
admin.site.register(models.NetworkDevice)
admin.site.register(models.IDC)
admin.site.register(models.BusinessUnit)
admin.site.register(models.Contract)
admin.site.register(models.CPU)
admin.site.register(models.Disk)
admin.site.register(models.NIC,NICAdmin)
admin.site.register(models.RAM)
admin.site.register(models.Manufactory)
admin.site.register(models.Tag)
admin.site.register(models.Software)
admin.site.register(models.EventLog,EventLogAdmin)
admin.site.register(models.NewAssetApprovalZone,NewAssetApprovalZoneAdmin)