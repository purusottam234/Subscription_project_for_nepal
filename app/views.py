from unittest import TextTestRunner
from django.shortcuts import render, redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import *
from .serializers import RegisterSerializer
from django.contrib.auth.hashers import make_password
from django.contrib import auth
import datetime
from datetime import timedelta
from datetime import datetime as dt
import requests
import json
from django.http import HttpResponseRedirect


today = datetime.date.today()


def home(request):
	return render(request, 'index.html')

def index(request):
	user_membership = UserMembership.objects.get(user=request.user)
	subscriptions = Subscription.objects.filter(user_membership=user_membership).exists()
	if subscriptions == False:
		return redirect('sub')
	else:
		subscription = Subscription.objects.filter(user_membership=user_membership).last()
		return render(request, 'home.html', {'sub': subscription})
	

def signin(request):
	return render(request, 'login.html')

def check_mail_ajax(request):
	if request.is_ajax():
		email = request.GET.get('email', None)
		check_email = User.objects.filter(email=email).exists()
		if check_email == True:
			response = {'error': 'Email already exists.'}
			return JsonResponse(response)
		else:
			response = {'success': 'Cool'}
			return JsonResponse(response)
	else:
		response = {'error': 'Error Email Checking.'}
		return JsonResponse(response)


class Register(APIView):
	def post(self, request):
		serializer = RegisterSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			obj = serializer.save()
			password = make_password(serializer.data['password'])
			User.objects.filter(email=serializer.data['email']).update(password=password)
			get_membership = Membership.objects.get(membership_type='Free')
			instance = UserMembership.objects.create(user=obj, membership=get_membership)
			return Response({'success': 'Registration successful.'})

		else:
			return Response({'error': 'Error. Try again'})


class Login(APIView):
	def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')

		# Let us check if the user exists or not...
		check_email = User.objects.filter(email=email).exists()
		if check_email == False:
			return Response({'error': 'No account with such email'})
		# We need to check if the user password is correct
		user = User.objects.get(email=email)
		if user.check_password(password) == False:
			return Response({'error': 'Password is not correct. Try again'})
		# Now let us log the user in
		log_user = auth.authenticate(email=email, password=password)
		if user is not None:
			auth.login(request, log_user)
			return Response({'success': 'Login successful'})
		else:
			return Response({'error': 'Invalid email/password. Try again later.'})


def subscription(request):
	return render(request, 'subscription.html')

def end_sub(request):
	return render(request, 'sub.html')


 

def subscribe(request):
	plan = request.GET.get('sub_plan')
	fetch_membership = Membership.objects.filter(membership_type=plan).exists()
	if fetch_membership == False:
		return redirect('subscribe')
	membership = Membership.objects.get(membership_type=plan)
	price = float(membership.price)  
	amount = int(price)
	
	instance = PayHistory.objects.create(amount= amount, payment_for=membership, user=request.user)
	
	context = {
		'instance': instance,
	}
	UserMembership.objects.filter(user=instance.user).update(membership=membership)
	return render(request, 'esewarequest.html',context)

class EsewaVerifyView(View):
    def get(self, request, *args, **kwargs):

        import xml.etree.ElementTree as ET                  

        oid = request.GET.get("oid")                        
        amt = request.GET.get("amt")                        
        refId = request.GET.get("refId")                    

        url = "https://uat.esewa.com.np/epay/transrec"      

        d = {                                               
            'amt': amt,
            'scd': 'epay_payment',
            'rid': refId,
            'pid': oid,
        }
        resp = requests.post(url, d)                        

        root = ET.fromstring(resp.content)                                                 

        status = root[0].text.strip()                       

        order_id = oid 
        order_obj = PayHistory.objects.get(id=order_id)

        if status == "Success":                             
            order_obj.paid = True
            order_obj.save()
            return redirect("/")
        else:                                               
            return redirect("/esewa-request/?o_id="+order_id)
                

# def call_back_url(request):
# 	reference = request.GET.get('reference')
# 	# We need to fetch the reference from PAYMENT
# 	check_pay = PayHistory.objects.filter(paystack_charge_id=reference).exists()
# 	if check_pay == False:
# 		# This means payment was not made error should be thrown here...
# 		print("Error")
# 	else:
# 		payment = PayHistory.objects.get(paid=reference)
# 		# We need to fetch this to verify if the payment was successful.
# 	def verify_payment(request):
# 		url = 'https://khalti.com/api/v2/payment/verify/'+ reference
# 		headers = {
# 				'Authorization': 'Key <your secret_key>',
# 				'Content-Type' : 'application/json',
# 				'Accept': 'application/json',
# 				}
# 		payload = {
# 				"reference": payment.paid
# 				}
# 		x = requests.get(url, data=json.dumps(payload), headers=headers)
# 		if x.status_code != 200:
# 			return str(x.status_code)
			
# 		results = x.json()
# 		return results

# 	initialized = verify_payment(request)
# 	if initialized['data']['status'] == 'success':
# 		PayHistory.objects.filter(paystack_charge_id=initialized['data']['reference']).update(paid=True)
# 		new_payment = PayHistory.objects.get(paystack_charge_id=initialized['data']['reference'])
# 		instance = Membership.objects.get(id=new_payment.payment_for.id)
# 		sub = UserMembership.objects.filter(reference_code=initialized['data']['reference']).update(membership=instance)
# 		user_membership = UserMembership.objects.get(reference_code=initialized['data']['reference'])
# 		Subscription.objects.create(user_membership=user_membership, expires_in=dt.now().date() + timedelta(days=user_membership.membership.duration))
# 		return redirect('subscribed')
# 	return render(request, 'payment.html')


def subscribed(request):
	return render(request, 'subscribed.html')