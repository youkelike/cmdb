from django.shortcuts import render,HttpResponse

# Create your views here.
import json
from assets import models
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt



