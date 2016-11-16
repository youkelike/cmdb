import json
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from assets import models

class Asset(object):
    def __init__(self,request):
        '''
        通过request接收用户数据，定义一些全局设置
        '''
        self.request = request
        # 检测传入数据中必须存在的字段
        self.mandatory_fields = ['sn','asset_id','asset_type']
        # 返回数据格式
        self.response = {
            'error':[],
            'info':[],
            'warning':[]
        }
        # 从数据库中取出的资产数据对象
        self.asset_obj = None
        # 用户传入的数据合法，就会赋值给这个变量
        self.clean_data = None
        # 标记传入的资产数据是否是新资产
        self.waiting_approval = False


    def response_msg(self,msg_type,key,msg):
        if msg_type in self.response:
            self.response[msg_type].append({key:msg})
        else:
            raise ValueError

    def mandatory_check(self,data,only_check_sn=False):
        '''
        先做数据合法性验证：只判断是否存在必须的字段
        通过验证后再尝试去数据库中匹配已有记录，匹配到了就取出数据对象，没匹配到就标记为新资产
        只有通过合法验证并取得数据库中的数据才返回True
        '''
        for field in self.mandatory_fields:
            if field not in data:
                self.response_msg('error','MandatoryCheckFailed','Field [%s] not provided!' % field)
        else:
            if self.response['error']:return False
        try:
            # 尝试取出数据对象
            if not only_check_sn:
                self.asset_obj = models.Asset.objects.get(id=int(data['asset_id']),sn=data['sn'])
            else:
                self.asset_obj = models.Asset.objects.get(sn=data['sn'])
            return True
        except ObjectDoesNotExist as e:
            self.response_msg('error','AssetDataInvalid','None asset matched by using asset id [%s] and SN [%s]' % (data['asset_id'],data['sn']))
            # 没匹配到就标记为新资产
            self.waiting_approval = True
            return False

    def get_asset_id_by_sn(self):
        '''
        处理提交的数据中没有asset_id的情况
        可能是新资产，也可能是资产asset_id丢失的情况
        :return:
        '''
        data = self.request.POST.get('asset_data')
        response = {}
        if data:
            try:
                data = json.loads(data)
                # 通过验证，一定会得到数据库中的数据对象，
                # 说明不是新资产，而是资产asset_id丢失了，返回asset_id
                if self.mandatory_check(data,only_check_sn=True):
                    response = {'asset_id':self.asset_obj.id}
                else:# 验证不通过则可能是新资产，也可能是数据无效
                    if hasattr(self,'waiting_approval'):
                        response = {'needs_approval':'this is a new asset, needs admin approval!'}
                        self.clean_data = data
                        # 把新资产数据存入资产审批表
                        self.save_new_asset_to_approval_zone()
                        print(response)
                    else:
                        response = self.response
            except ValueError as e:
                self.response_msg('error','AssetDataInvalid',str(e))
                response = self.response
        else:
            self.response_msg('error','AssetDataInvalid','The reported asset data is not valid or provided!')
            response = self.response
        return response

    def save_new_asset_to_approval_zone(self):
        '''
        把数据加入到资产审批表
        :return:
        '''
        asset_sn = self.clean_data.get('sn')
        # 只在第一次新资产提交时才会被加入到审批表
        asset_already_in_approval_zone,created = models.NewAssetApprovalZone.objects.update_or_create(sn=asset_sn,
                                                                                                      defaults={'data':json.dumps(self.clean_data),
                                                                                                        'manufactory':self.clean_data.get('manufactory'),
                                                                                                        'model':self.clean_data.get('model'),
                                                                                                        'asset_type':self.clean_data.get('asset_type'),
                                                                                                        'ram_size':sum(i['capacity'] if 'capacity' in i else 0 for i in self.clean_data.get('ram')),
                                                                                                        'cpu_model':self.clean_data.get('cpu_model'),
                                                                                                        'cpu_count':self.clean_data.get('cpu_count'),
                                                                                                        'cpu_core_count':self.clean_data.get('cpu_core_count'),
                                                                                                        'os_distribution':self.clean_data.get('os_distribution'),
                                                                                                        'os_release':self.clean_data.get('os_release'),
                                                                                                        'os_type':self.clean_data.get('os_type'),
                                                                                                      }

                                                                                           )
        print('****created',created)
        return True

    def data_is_valid(self):
        '''
        提交带有asset_id资产的数据合法性验证
        只有数据合法，并且从数据库中匹配到了资产才会返回True
        '''
        data = self.request.POST.get('asset_data')
        if data:
            try:
                data = json.loads(data)
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error','AssetDataInvalid','The reported asset data is not valid!')

    def __is_new_asset(self):
        '''
        Asset表中的的数据属于业务数据，可以手动录入。
        这就存在一种情况：可以通过sn或asset_id找到Asset表中的记录，这条Asset记录却没有关联任何设备。
        所以不能仅仅通过是否匹配到Asset记录来判断是否为新资产，还要看它是否关联了某种设备
        '''
        if not hasattr(self.asset_obj,self.clean_data['asset_type']):
            return True
        else:
            return False

    def data_inject(self):
        '''
        根据需要插入或更新资产数据
        :return:
        '''
        if self.__is_new_asset():
            print('\033[32;1m--- new asset going to create --- \033[0m')
            self.create_asset()
        else:
            print('\033[33;1m--- asset already exists going to update ---\033[0m')
            self.update_asset()

    def data_is_valid_without_id(self):
        data = self.request.POST.get('asset_data')
        if data:
            try:
                data = json.loads(data)
                asset_obj = models.Asset.objects.get_or_create(sn=data.get('sn'),name=data.get('sn'))
                data['asset_id'] = asset_obj[0].id
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error','AssetDataInvalid',str(e))
        else:
            self.response_msg('error','AssetDataInvalid','The reported asset data is invalid!')

    def __verify_field(self,data_set,field_key,data_type,required=True):
        '''
        验证数据对象中的某个属性是否必须存在，属性的值类型是否匹配、
        '''
        field_val = data_set.get(field_key)
        if field_val or field_val==0:
            try:
                data_set[field_key] = data_type(field_val)
            except ValueError as e:
                self.response_msg('error','InvalidField','The field [%s] id invalid, the correct data type should be [%s]!' % (field_key,data_type))
        elif required == True:
            self.response_msg('error','LackOfField','The field [%s] not provided in [%s]' % (field_key,data_set))

    def create_asset(self):
        '''使用反射机制调用新建资产方法'''
        func = getattr(self,'_create_%s' % self.clean_data['asset_type'])
        create_obj = func()

    def update_asset(self):
        '''使用反射机制调用更新资产方法'''
        func = getattr(self,'_update_%s' % self.clean_data['asset_type'])
        create_obj = func()

    def _update_server(self):
        nic = self.__update_asset_component(data_source=self.clean_data['nic'],
                                            fk='nic_set',
                                            update_fields=['name','sn','model','macaddress','ipaddress','netmask','bonding'],
                                            identify_field='macaddress'
                                            )
        disk = self.__update_asset_component(data_source=self.clean_data['physical_disk_driver'],
                                             fk='disk_set',
                                             update_fields=['slot','sn','model','manufactory','capacity','iface_type'],
                                             identify_field='slot'
                                             )
        ram = self.__update_asset_component(data_source=self.clean_data['ram'],
                                            fk='ram_set',
                                            update_fields=['slot','sn','model','capacity'],
                                            identify_field='slot'
                                            )
        cpu = self.__update_cpu_component()
        manufactory = self.__update_manufactory_component()
        server = self.__update_server_component()

    def _create_server(self):
        '''
        新建资产包括了在各种关联表中新建记录
        '''
        self.__create_server_info()
        self.__create_or_update_manufactory()
        self.__create_cpu_component()
        self.__create_disk_component()
        self.__create_nic_component()
        self.__create_ram_component()
        log_msg = 'Asset[<a href="/admin/assets/asset/%s/" target="_blank">%s</a>] has been created!' % (self.asset_obj.id,self.asset_obj)
        self.response_msg('info','NewAssetOnline',log_msg)

    def __create_server_info(self,ignore_errs=False):
        try:
            self.__verify_field(self.clean_data,'model',str)
            if not len(self.response['error']) or ignore_errs == True:
                data_set = {
                    'asset_id':self.asset_obj.id,
                    'raid_type':self.clean_data.get('raid_type'),
                    'model':self.clean_data.get('model'),
                    'os_type':self.clean_data.get('os_type'),
                    'os_distribution':self.clean_data.get('os_distribution'),
                    'os_release':self.clean_data.get('os_release'),
                }
                obj = models.Server(**data_set)
                obj.save()
                return obj
        except Exception as e:
            self.response_msg('error','ObjectCreationException','Object [server] %s' % str(e))

    def __create_or_update_manufactory(self,ignore_errs=False):
        try:
            self.__verify_field(self.clean_data,'manufactory',str)
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs:
                obj_exist = models.Manufactory.objects.filter(name=manufactory)
                if obj_exist:
                    obj = obj_exist[0]
                else:
                    obj = models.Manufactory(name=manufactory)
                    obj.save()
                self.asset_obj.manufactory = obj
                self.asset_obj.save()
        except Exception as e:
            self.response_msg('error','ObjectCreationException','Object [manufactory] %s ' % str(e))

    def __create_cpu_component(self,ignore_errs=False):
        '''cpu只有一个'''
        try:
            self.__verify_field(self.clean_data,'model',str),
            self.__verify_field(self.clean_data,'cpu_count',int),
            self.__verify_field(self.clean_data,'cpu_core_count',int),
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_id':self.asset_obj.id,
                    'cpu_model':self.clean_data.get('cpu_model'),
                    'cpu_count':self.clean_data.get('cpu_count'),
                    'cpu_core_count':self.clean_data.get('cpu_core_count'),
                }
                obj = models.CPU(**data_set)
                obj.save()
                log_msg = 'Asset[%s] --> has added new [cpu] component with data [%s]' % (self.asset_obj,data_set)
                self.response_msg('info','NewComponentAdded',log_msg)
                return obj
        except Exception as e:
            self.response_msg('error','ObjectCreationException','Object [cpu] %s' % str(e))

    def __create_disk_component(self):
        '''磁盘可能有多个'''
        disk_info = self.clean_data.get('physical_disk_driver')
        print('*****disk info:',disk_info)
        if disk_info:
            obj_arr = []
            for disk_item in disk_info:
                try:
                    self.__verify_field(disk_item,'slot',str)
                    self.__verify_field(disk_item,'capacity',float)
                    self.__verify_field(disk_item,'iface_type',str)
                    self.__verify_field(disk_item,'model',str)
                    if not len(self.response['error']):
                        data_set = {
                            'asset_id':self.asset_obj.id,
                            'sn':disk_item.get('sn'),
                            'slot':disk_item.get('slot'),
                            'capacity':disk_item.get('capacity'),
                            'model':disk_item.get('model'),
                            'iface_type':disk_item.get('iface_type'),
                            'manufactory':disk_item.get('manufactory')
                        }
                        obj = models.Disk(**data_set)
                        obj_arr.append(obj)
                        # obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [disk] %s' % str(e))
            # 批量创建
            if len(obj_arr>0):
                models.Disk.objects.bulk_create(*obj_arr)
        else:
            self.response_msg('error', 'LackOfData', 'Disk info is not provied in your reporting data')

    def __create_nic_component(self):
        '''网卡可能有多个'''
        nic_info = self.clean_data.get('nic')
        if nic_info:
            obj_arr = []
            for nic_item in nic_info:
                try:
                    self.__verify_field(nic_item,'macaddress',str)
                    if not len(self.response['error']): #no processing when there's no error happend
                        data_set = {
                            'asset_id' : self.asset_obj.id,
                            'name': nic_item.get('name'),
                            'sn': nic_item.get('sn'),
                            'macaddress':nic_item.get('macaddress'),
                            'ipaddress':nic_item.get('ipaddress'),
                            'bonding':nic_item.get('bonding'),
                            'model':nic_item.get('model'),
                            'netmask':nic_item.get('netmask'),
                        }

                        obj = models.NIC(**data_set)
                        # obj.save()
                        obj_arr.append(obj)
                except Exception as e:
                    self.response_msg('error','ObjectCreationException','Object [nic] %s' % str(e) )
            # 批量创建
            if len(obj_arr>0):
                models.NIC.objects.bulk_create(*obj_arr)
        else:
            self.response_msg('error', 'LackOfData', 'NIC info is not provied in your reporting data')

    def __create_ram_component(self):
        '''内存可能有多个'''
        ram_info = self.clean_data.get('ram')
        if ram_info:
            obj_arr = []
            for ram_item in ram_info:
                try:
                    self.__verify_field(ram_item,'capacity',int)
                    if not len(self.response['error']): #no processing when there's no error happend
                        data_set = {
                            'asset_id' : self.asset_obj.id,
                            'slot': ram_item.get("slot"),
                            'sn': ram_item.get('sn'),
                            'capacity':ram_item.get('capacity'),
                            'model':ram_item.get('model'),
                        }

                        obj = models.RAM(**data_set)
                        # obj.save()
                        obj_arr.append(obj)
                except Exception as e:
                    self.response_msg('error','ObjectCreationException','Object [ram] %s' % str(e) )
            # 批量创建
            if len(obj_arr>0):
                models.RAM.objects.bulk_create(*obj_arr)
        else:
                self.response_msg('error','LackOfData','RAM info is not provied in your reporting data' )

    def __update_server_component(self):
        update_fields = ['model','raid_type','os_type','os_distribution','os_release']
        if hasattr(self.asset_obj,'server'):
            self.__compare_component(model_obj=self.asset_obj.server,
                                     fields_from_db=update_fields,
                                     data_source=self.clean_data)
        else:
            self.__create_server_info(ignore_errs=True)

    def __update_manufactory_component(self):
        self.__create_or_update_manufactory(ignore_errs=True)

    def __update_cpu_component(self):
        update_fields = ['cpu_model','cpu_count','cpu_core_count']
        if hasattr(self.asset_obj,'cpu'):
            self.__compare_component(model_obj=self.asset_obj.cpu,
                                     fields_from_db=update_fields,
                                     data_source=self.clean_data)
        else:
            self.__create_cpu_component(ignore_errs=True)

    def __update_asset_component(self,data_source,fk,update_fields,identify_field=None):
        try:
            component_obj = getattr(self.asset_obj,fk)
            if hasattr(component_obj,'select_related'):
                objects_from_db = component_obj.select_related()
                for obj in objects_from_db:
                    key_field_data = getattr(obj,identify_field)
                    if type(data_source) is list:
                        for source_data_item in data_source:
                            key_field_data_from_source_data = source_data_item.get(identify_field)
                            if key_field_data_from_source_data:
                                if key_field_data == key_field_data_from_source_data:
                                    self.__compare_component(model_obj=obj,fields_from_db=update_fields,data_source=source_data_item)
                                    break
                            else:
                                self.response_msg('warning',
                                                  'AssetUpdateWarning',
                                                  "Asset component [%s]'s key field [%s] is not provided in reporting data " % (fk,identify_field))
                        else:
                            print('\033[33;1mError:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!\033[0m' % (
                            key_field_data))
                            self.response_msg("error",
                                              "AssetUpdateWarning",
                                              "Cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!" % key_field_data)

                    elif type(data_source) is dict:
                        for key,source_data_item in data_source.items():
                            key_field_data_from_source_data = source_data_item.get(identify_field)
                            if key_field_data_from_source_data:
                                if key_field_data == key_field_data_from_source_data:
                                    self.__compare_component(model_obj=obj,fields_from_db=update_fields,data_source=source_data_item)
                                    break
                            else:
                                self.response_msg('warning', 'AssetUpdateWarning',
                                                  "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                                  fk, identify_field))
                        else:
                            print('\033[33;1mWarning:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!\033[0m' % key_field_data)
                    else:
                        print('\033[31;1mMust be sth wrong,logic should goes to here at all.\033[0m')
                self.__filter_add_or_deleted_components(model_obj_name=component_obj.model._meta.object_name,data_from_db=objects_from_db,data_source=data_source,identify_field=identify_field)
            else:
                pass
        except ValueError as e:
            print('\033[41;1m%s\033[0m' % str(e))

    def __filter_add_or_deleted_components(self,model_obj_name,data_from_db,data_source,identify_field):
        data_source_key_list = []
        if type(data_source) is list:
            for data in data_source:
                data_source_key_list.append(data.get(identify_field))
        elif type(data_source) is dict:
            for key,data in data_source.items():
                if data.get(identify_field):
                    data_source_key_list.append(data.get(identify_field))
                else:
                    data_source_key_list.append(key)
        print('-->identify field [%s] from db  :', data_source_key_list)
        print('-->identify[%s] from data source:', [getattr(obj, identify_field) for obj in data_from_db])
        data_source_key_list = set(data_source_key_list)
        data_identify_val_from_db = set([getattr(obj,identify_field) for obj in data_from_db])
        data_only_in_db = data_identify_val_from_db - data_source_key_list
        data_only_in_data_source = data_source_key_list - data_identify_val_from_db
        print('\033[31;1mdata_only_in_db:\033[0m', data_only_in_db)
        print('\033[31;1mdata_only_in_data source:\033[0m', data_only_in_data_source)
        self.__delete_components(all_components=data_from_db,delete_list=data_only_in_db,identify_field=identify_field)
        if data_only_in_data_source:
            self.__add_components(model_obj_name=model_obj_name,all_components=data_source,add_list=data_only_in_data_source,identify_field=identify_field)

    def __add_components(self,model_obj_name,all_components,add_list,identify_field):
        model_class = getattr(models,model_obj_name)
        will_be_creating_list = []
        print('--- add component list: %s ---' % add_list)
        if type(all_components) is list:
            for data in all_components:
                if data[identify_field] in add_list:
                    will_be_creating_list.append(data)
        elif type(all_components) is dict:
            for k,data in all_components.items():
                if data.get(identify_field):
                    if data[identify_field] in add_list:
                        will_be_creating_list.append(data)
        try:
            for component in will_be_creating_list:
                data_set = {}
                for field in model_class.auto_create_fields:
                    data_set[field] = component.get(field)
                data_set['asset_id'] = self.asset_obj.id
                obj = model_class(**data_set)
                obj.save()
                print('\033[32;1mCreated component with data:\033[0m', data_set)
                log_msg = "Asset[%s] --> component[%s] has justed added a new item [%s]" % (self.asset_obj, model_obj_name, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                log_handler(self.asset_obj, 'NewComponentAdded', self.request.user, log_msg, model_obj_name)
        except Exception as e:
            print("\033[31;1m %s \033[0m"  % e)
            log_msg = "Asset[%s] --> component[%s] has error: %s" %(self.asset_obj,model_obj_name,str(e))
            self.response_msg('error',"AddingComponentException",log_msg)

    def __delete_components(self,all_components,delete_list,identify_field):
        deleting_obj_list = []
        print('--- deleting components',delete_list,identify_field)
        for obj in all_components:
            val = getattr(obj,identify_field)
            if val in delete_list:
                deleting_obj_list.append(obj)
        for i in deleting_obj_list:
            log_msg = "Asset[%s] --> component[%s] --> is lacking from reporting source data, assume it has been removed or replaced,will also delete it from DB" % (self.asset_obj, i)
            self.response_msg('info', 'HardwareChanges', log_msg)
            log_handler(self.asset_obj, 'HardwareChanges', self.request.user, log_msg, i)
            i.delete()

    def __compare_component(self,model_obj,fields_from_db,data_source):
        for field in fields_from_db:
            val_from_db = getattr(model_obj,field)
            val_from_data_source = data_source.get(field)
            if val_from_data_source:
                if type(val_from_db) is str:val_from_data_source = str(val_from_data_source)
                elif type(val_from_db) is int:val_from_data_source = int(val_from_data_source)
                elif type(val_from_db) is float:val_from_data_source = float(val_from_data_source)
                if val_from_db == val_from_data_source:
                    pass
                else:
                    print('\033[34;1m val_from_db[%s]  != val_from_data_source[%s]\033[0m' %(val_from_db,val_from_data_source),type(val_from_db),type(val_from_data_source))
                    db_field = model_obj._meta.get_field(field)
                    db_field.save_form_data(model_obj,val_from_data_source)
                    model_obj.update_date = timezone.now()
                    model_obj.save()
                    log_msg = "Asset[%s] --> component[%s] --> field[%s] has changed from [%s] to [%s]" % (self.asset_obj, model_obj, field, val_from_db, val_from_data_source)
                    self.response_msg('info', 'FieldChanged', log_msg)
                    log_handler(self.asset_obj, 'FieldChanged', self.request.user, log_msg, model_obj)
            else:
                self.response_msg('warning','AssetUpdateWarning',"Asset component [%s]'s field [%s] is not provided in reporting data " % (model_obj,field) )

        model_obj.save()

def log_handler(asset_obj,event_name,user,detail,component=None):
    log_catelog = {
        1:['FieldChanged','HardwareChanges'],
        2:['NewComponentAdded']
    }
    if not user.id:
        user = models.UserProfile.objects.filter(is_admin=True).last()
    event_type = None
    for k,v in log_catelog.items():
        if event_name in v:
            event_type = k
            break
    log_obj = models.EventLog(
        name=event_name,
        event_type=event_type,
        asset_id=asset_obj.id,
        component=component,
        user_id=user.id
    )
    log_obj.save()