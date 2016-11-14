from django.shortcuts import render,HttpResponse,HttpResponseRedirect
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
import django

@login_required
def index(request):
    return render(request,'index.html')

def acc_login(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        #账号验证
        user = auth.authenticate(username=username,password=password)
        if user is not None:
            if django.utils.timezone.now()>user.valid_begin_time and django.utils.timezone.now()<user.valid_end_time:
                #登录创建session
                auth.login(request,user)
                #设置session有效期
                request.session.set_expiry(60*30)
                return HttpResponseRedirect('/')
            else:
                return render(request,'login',{'login_err':'Account is expired!'})
        else:
            return render(request,'login.html',{'login_err':'Wrong username or password!'})
    else:
        return render(request,'login.html')