from django.conf.urls import url,include
from rest_framework import routers
from assets import rest_views as views

router = routers.DefaultRouter()
router.register(r'users',views.UserViewSet)
router.register(r'assets',views.AssetViewSet)
router.register(r'servers',views.ServerViewSet)
router.register(r'manufactorys',views.ManufactoryViewSet)
router.register(r'ram',views.RAMViewSet)

urlpatterns = [
    url(r'^',include(router.urls)),#restframework的方式
    url(r'^asset_list/',views.AssetList),#django的方式
    url(r'^api-auth/',include('rest_framework.urls',namespace='rest_framework'))
]