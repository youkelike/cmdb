from django.db import models

# Create your models here.
from assets.myauth import UserProfile
from django.utils.html import format_html

'''
    资产表里保存的是服务器、网络设备的通用信息，与它们是反向一对一关系
    资产与业务线之间是多对一的关系，业务线可以包含子业务线，还可以给业务线中的设备打上标签
    服务器或者网络设备中的网卡、cpu、内存、硬盘参数差别大，各自建表，但都直接建立关联到Asset
    键盘、鼠标、网线、显示器等参数不能自动获取，为了简化不算资产不录入系统
    资产上可能有软件配置（免费软件不应算资产）,用ontoone关联到单独的配置表
'''
class Asset(models.Model):

    asset_type_choices = (
        ('server',u'服务器'),
        ('switch',u'服务器'),
        ('router',u'服务器'),
        ('firewall',u'服务器'),
        ('storage',u'服务器'),
        ('NLB',u'服务器'),
        ('wireless',u'服务器'),
        ('software',u''),
        ('others',u'其它类'),
    )
    asset_type = models.CharField(u'资产类型',choices=asset_type_choices,max_length=32,default='server')
    name = models.CharField(u'名称',max_length=64,unique=True)
    sn = models.CharField(u'资产SN号',max_length=128,unique=True)
    manufactory = models.ForeignKey('Manufactory',verbose_name=u'制造商',blank=True,null=True)
    management_ip = models.GenericIPAddressField(u'管理IP',blank=True,null=True)
    contract = models.ForeignKey('Contract',verbose_name=u'合同',blank=True,null=True)
    trade_date = models.DateTimeField(u'购买时间',blank=True,null=True)
    expire_date = models.DateTimeField(u'过保修期',blank=True,null=True)
    price = models.FloatField(u'价格',blank=True,null=True)
    business_unit = models.ForeignKey('BusinessUnit',verbose_name=u'所属业务线',blank=True,null=True)
    tags = models.ManyToManyField('Tag',blank=True)
    admin = models.ForeignKey('UserProfile',verbose_name=u'资产管理员',blank=True,null=True)
    idc = models.ForeignKey('IDC',verbose_name=u'IDC机房',blank=True,null=True)
    memo = models.TextField(u'备注',blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间',blank=True,null=True)
    update_date = models.DateTimeField(u'更新时间',blank=True,null=True)

    class Meta:
        verbose_name = u'资产总表'
        verbose_name_plural = u'资产总表'
    def __str__(self):
        return 'id:%s name:%s' % (self.id,self.name)

class Server(models.Model):
    asset = models.OneToOneField('Asset')
    created_by_choices = (
        ('auto','Auto'),
        ('manual','Manual'),
    )
    created_by = models.CharField(u'创建方式',choices=created_by_choices,max_length=32,default='auto')
    #为虚拟主机预留的自关联字段
    hosted_on = models.ForeignKey('self',related_name='hosted_on_server',blank=True,null=True)
    #不同设备型号格式不一样不适合统一放到Asset
    model = models.CharField(u'型号',max_length=128,blank=True,null=True)
    raid_type = models.CharField(u'raid类型',max_length=512,blank=True,null=True)
    os_type = models.CharField(u'操作系统类型',max_length=32,blank=True,null=True)
    os_distribution = models.CharField(u'发行版本',max_length=32,blank=True,null=True)
    os_release = models.CharField(u'操作系统版本',max_length=32,blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间',blank=True,auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间',blank=True,null=True)

    class Meta:
        verbose_name = u'服务器'
        verbose_name_plural = u'服务器'
    def __str__(self):
        return '%s sn:%s' % (self.asset.name,self.asset.sn)

class NetworkDevice(models.Model):
    asset = models.OneToOneField('Asset')
    vlan_ip = models.GenericIPAddressField(u'VlanIP',blank=True,null=True)
    intranet_ip = models.GenericIPAddressField(u'内网IP',blank=True,null=True)
    model = models.CharField(u'型号',max_length=128,blank=True,null=True)
    firmware = models.CharField(u'固件',max_length=128,blank=True,null=True)
    port_num = models.SmallIntegerField(u'端口个数',blank=True,null=True)
    device_detail = models.TextField(u'设置详细配置',blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间', blank=True, auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间', blank=True, null=True)

    class Meta:
        verbose_name = u'网络设备'
        verbose_name_plural = u'网络设备'
    def __str__(self):
        return '%s sn:%s' % (self.asset.name,self.asset.sn)

class Software(models.Model):
    os_type_choices = (
        ('linux','Linux'),
        ('windows','Windows'),
        ('network_firmware','Network Firmware'),
        ('software','Software'),
    )
    os_distribution_choices = (
        ('windows','Windows'),
        ('centos','CentOS'),
        ('ubuntu','Ubuntu'),
    )
    os_type = models.CharField(u'系统类型',choices=os_type_choices,max_length=32,help_text='eg. GNU/Linux',default='linux')
    os_distribution = models.CharField(u'发行版本',choices=os_distribution_choices,max_length=32,default='windows')
    version = models.CharField(u'软件/系统版本',max_length=64,help_text=u'eg. CentOS release 6.5 (Final)',unique=True)
    language_choices = (
        ('cn',u'中文'),
        ('en',u'英文'),
    )
    language = models.CharField(u'软件/系统语言',choices=language_choices,max_length=32,default='en')

    class Meta:
        verbose_name = u'软件/系统'
        verbose_name_plural = u'软件/系统'
    def __str__(self):
        return self.version

class CPU(models.Model):
    '''
    cpu和其它硬件不同，一个机器上只能有一种型号的cpu,只会有核心数的不同，所以与asset建立一对一关系
    '''
    asset = models.OneToOneField('Asset')
    cpu_model = models.CharField(u'CPU型号',max_length=128,blank=True,null=True)
    cpu_count = models.SmallIntegerField(u'物理CPU个数',blank=True,null=True)
    cpu_core_count = models.SmallIntegerField(u'CPU核心数',blank=True,null=True)
    memo = models.TextField(u'备注',blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间', blank=True, auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间', blank=True, null=True)

    class Meta:
        verbose_name = u'CPU'
        verbose_name_plural = u'CPU'
    def __str__(self):
        return self.cpu_model

class RAM(models.Model):
    asset = models.ForeignKey('Asset')
    #多对一关联到asset，必须有自己的唯一标识sn,但可能获取不到，用slot来做唯一标识更好
    sn = models.CharField(u'SN号',max_length=128,blank=True, null=True)
    model = models.CharField(u'内存型号',max_length=128)
    slot = models.CharField(u'插槽',max_length=64)
    capacity = models.IntegerField(u'内存大小(MB)')
    memo = models.TextField(u'备注',blank=True, null=True)
    create_date = models.DateTimeField(u'创建时间', blank=True, auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间', blank=True, null=True)

    class Meta:
        verbose_name = u'内存'
        verbose_name_plural = u'内存'
        unique_together = ('asset','slot')
    auto_create_fields = ['sn','slot','model','capacity']

    def __str__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id,self.slot,self.capacity)

class Disk(models.Model):
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号',max_length=128,blank=True,null=True)
    slot = models.CharField(u'插槽位',max_length=64)
    manufactory = models.CharField(u'制造商',max_length=64,blank=True,null=True)
    model = models.CharField(u'磁盘型号',max_length=128,blank=True,null=True)
    capacity = models.IntegerField(u'磁盘容量GB')
    iface_type_choice = (
        ('SATA','SATA'),
        ('SAS','SAS'),
        ('SCSI','SCSI'),
        ('SSD','SSD'),
    )
    iface_type = models.CharField(u'接口类型',choices=iface_type_choice,max_length=32,default='SAS')
    memo = models.TextField(u'备注',blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间', blank=True,auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间',blank=True,null=True)

    class Meta:
        verbose_name = u'磁盘'
        verbose_name_plural = u'磁盘'
        unique_together = ("asset", "slot")
    auto_create_fields = ['sn', 'slot', 'manufactory', 'model','capacity','iface_type']

    def __str__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id, self.slot, self.capacity)

class NIC(models.Model):
    '''
    网卡的MAC必须是唯一的
    '''
    asset = models.ForeignKey('Asset')
    name = models.CharField(u'网卡名',max_length=64,blank=True,null=True)
    sn = models.CharField(u'SN号',max_length=128,blank=True,null=True)
    model = models.CharField(u'网卡型号',max_length=128,blank=True,null=True)
    macaddress = models.CharField(u'MAC',max_length=64,unique=True)
    ipaddress = models.GenericIPAddressField(u'IP',blank=True,null=True)
    netmask = models.CharField(u'掩码',max_length=32,blank=True,null=True)
    bonding = models.CharField(max_length=64,blank=True,null=True)
    memo = models.TextField(u'备注',blank=True,null=True)
    create_date = models.DateTimeField(u'创建时间', blank=True, auto_now_add=True)
    update_date = models.DateTimeField(u'更新时间', blank=True, null=True)

    class Meta:
        verbose_name = u'网卡'
        verbose_name_plural = u'网卡'

    auto_create_fields = ['sn', 'name', 'model', 'macaddress', 'ipaddress','netmask','bonding']

    def __str__(self):
        return '%s:%s' % (self.asset_id, self.macaddress)

class RaidAdaptor(models.Model):
    asset = models.ForeignKey('Asset')
    sn = models.CharField(u'SN号', max_length=128, blank=True, null=True)
    slot = models.CharField(u'插口', max_length=64)
    model = models.CharField(u'型号', max_length=64, blank=True, null=True)
    memo = models.TextField(u'备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = u'RAID设备'
        verbose_name_plural = u'RAID设备'
        unique_together = ("asset", "slot")
    def __str__(self):
        return self.name

class Manufactory(models.Model):
    name = models.CharField(u'厂商名称',max_length=64, unique=True)
    support_num = models.CharField(u'支持电话',max_length=30,blank=True)
    memo = models.CharField(u'备注',max_length=128,blank=True)

    class Meta:
        verbose_name = u'厂商'
        verbose_name_plural = u"厂商"
    def __str__(self):
        return self.name

class BusinessUnit(models.Model):
    #自关联
    parent_unit = models.ForeignKey('self',related_name='parent_level',blank=True,null=True)
    name = models.CharField(u'业务线',max_length=64, unique=True)
    memo = models.CharField(u'备注',max_length=64, blank=True)

    class Meta:
        verbose_name = u'业务线'
        verbose_name_plural = u"业务线"
    def __str__(self):
        return self.name

class Contract(models.Model):
    sn = models.CharField(u'合同号', max_length=128,unique=True)
    name = models.CharField(u'合同名称', max_length=64 )
    memo = models.TextField(u'备注', blank=True,null=True)
    price = models.IntegerField(u'合同金额')
    detail = models.TextField(u'合同详细',blank=True,null=True)
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    license_num = models.IntegerField(u'license数量',blank=True)
    create_date = models.DateField(auto_now_add=True)
    update_date= models.DateField(auto_now=True)
    class Meta:
        verbose_name = u'合同'
        verbose_name_plural = u"合同"
    def __str__(self):
        return self.name

class IDC(models.Model):
    name = models.CharField(u'机房名称',max_length=64,unique=True)
    memo = models.CharField(u'备注',max_length=128)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = u'机房'
        verbose_name_plural = u"机房"

class Tag(models.Model):
    name = models.CharField('Tag name',max_length=32,unique=True )
    creater = models.ForeignKey('UserProfile')
    create_date = models.DateField(auto_now_add=True)
    class Meta:
        verbose_name = u'标签'
        verbose_name_plural = u"标签"
    def __str__(self):
        return self.name

class EventLog(models.Model):
    name = models.CharField(u'事件名称', max_length=100)
    event_type_choices = (
        (1,u'硬件变更'),
        (2,u'新增配件'),
        (3,u'设备下线'),
        (4,u'设备上线'),
        (5,u'定期维护'),
        (6,u'业务上线\更新\变更'),
        (7,u'其它'),
    )
    event_type = models.SmallIntegerField(u'事件类型', choices= event_type_choices)
    asset = models.ForeignKey('Asset')
    component = models.CharField('事件子项',max_length=255, blank=True,null=True)
    detail = models.TextField(u'事件详情')
    date = models.DateTimeField(u'事件时间',auto_now_add=True)
    user = models.ForeignKey('UserProfile',verbose_name=u'事件源')
    memo = models.TextField(u'备注', blank=True,null=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = u'事件记录'
        verbose_name_plural = u"事件记录"

    #后台自定义展示列
    def colored_event_type(self):
        if self.event_type == 1:
            cell_html = '<span style="background: orange;">%s</span>'
        elif self.event_type == 2 :
            cell_html = '<span style="background: yellowgreen;">%s</span>'
        else:
            cell_html = '<span >%s</span>'
        return format_html(cell_html % self.get_event_type_display())
    colored_event_type.allow_tags = True
    colored_event_type.short_description = u'事件类型'

class NewAssetApprovalZone(models.Model):
    sn = models.CharField(u'资产SN号',max_length=128, unique=True)
    asset_type_choices = (
        ('server', u'服务器'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('firewall', u'防火墙'),
        ('storage', u'存储设备'),
        ('NLB', u'NetScaler'),
        ('wireless', u'无线AP'),
        ('software', u'软件资产'),
        ('others', u'其它类'),
    )
    asset_type = models.CharField(choices=asset_type_choices,max_length=64,blank=True,null=True)
    manufactory = models.CharField(max_length=64,blank=True,null=True)
    model = models.CharField(max_length=128,blank=True,null=True)
    ram_size = models.IntegerField(blank=True,null=True)
    cpu_model = models.CharField(max_length=128,blank=True,null=True)
    cpu_count = models.IntegerField(blank=True,null=True)
    cpu_core_count = models.IntegerField(blank=True,null=True)
    os_distribution =  models.CharField(max_length=64,blank=True,null=True)
    os_type =  models.CharField(max_length=64,blank=True,null=True)
    os_release =  models.CharField(max_length=64,blank=True,null=True)
    data = models.TextField(u'资产数据')
    date = models.DateTimeField(u'汇报日期',auto_now_add=True)
    approved = models.BooleanField(u'已批准',default=False)
    approved_by = models.ForeignKey('UserProfile',verbose_name=u'批准人',blank=True,null=True)
    approved_date = models.DateTimeField(u'批准日期',blank=True,null=True)

    def __str__(self):
        return self.sn
    class Meta:
        verbose_name = u'新上线待批准资产'
        verbose_name_plural = u"新上线待批准资产"




