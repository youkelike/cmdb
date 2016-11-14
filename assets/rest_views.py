from rest_framework import viewsets
from rest_framework import status
from rest_framework import permissions
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response

from assets import myauth
from assets import models
from assets.serializers import UserSerializer,AssetSerializer,ServerSerializer,ManufactorySerializer,RAMSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = myauth.UserProfile.objects.all()
    # 自定义的数据格式化类
    # 从数据库中取出的queryset是python对象，必须格式化成前端能处理的json格式
    # 同时也做POST数据验证，会自动根据表结构定义去验证传入的数据
    serializer_class = UserSerializer

class AssetViewSet(viewsets.ModelViewSet):
    queryset = models.Asset.objects.all()
    serializer_class = AssetSerializer

class ServerViewSet(viewsets.ModelViewSet):
    queryset = models.Server.objects.all()
    serializer_class = ServerSerializer

class ManufactoryViewSet(viewsets.ModelViewSet):
    queryset = models.Manufactory.objects.all()
    serializer_class = ManufactorySerializer

class RAMViewSet(viewsets.ModelViewSet):
    queryset = models.RAM.objects.all()
    serializer_class = RAMSerializer


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def AssetList(request):
    if request.method == 'GET':
        asset_list = models.Asset.objects.all()
        serializer = AssetSerializer(asset_list,many=True)
        print(serializer.data)
        #使用restframework封装的Response
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AssetSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)