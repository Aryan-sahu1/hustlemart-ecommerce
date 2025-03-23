from django.shortcuts import redirect, render
from ecommerceapp.models import Contact,Product,Orders,OrderUpdate
from django.contrib import messages
from ecommerceapp import keys
from django.conf import settings
MERCHANT_KEY=keys.MK
import json
from django.views.decorators.csrf import csrf_exempt 
from PayTm import Checksum
from math import ceil

def index(request):
    allProds=[]
    catProds= Product.objects.values('category','id')
    cats= {item['category'] for item in catProds}
    for cat in cats:
        prod=Product.objects.filter(category=cat)
        n=len(prod)
        nSlides= n//4 + ceil(n/4)-(n//4)
        allProds.append([prod,range(1,nSlides), nSlides])
    
    params={'allProds':allProds}
    return render(request,'index.html',params)

 
 
def contact(request):
    if request.method=="POST":
        name=request.POST.get("name")
        email=request.POST.get("email")
        desc=request.POST.get("desc")
        phonen=request.POST.get("phonen")
        myquery=Contact(name=name,email=email,desc=desc,phonenumber=phonen)
        myquery.save()
        messages.info(request,"We will get back you soon..")
        return render(request,"contact.html")
        
    return render(request,'contact.html')
 
def about(request):
    return render(request,'about.html')

def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Login & try Again")
        return redirect('/auth/login')
    
    if request.method=="POST":
        items_json= request.POST.get('itemsJson','')    
        name= request.POST.get('name','')    
        amount= request.POST.get('amt','')    
        email= request.POST.get('email','')    
        address1= request.POST.get('address1','')    
        address2= request.POST.get('address2','')    
        city= request.POST.get('city','')    
        state= request.POST.get('state','')    
        zip_code= request.POST.get('zip_code','')    
        phone= request.POST.get('phone','')    
        Order= Orders(items_json=items_json,name=name,email=email,amount=amount,address1=address1,address2=address2,city=city,state=state,zip_code=zip_code,phone=phone) 
        print(amount)
        Order.save();  
        update=OrderUpdate(order_id=Order.order_id,update_desc="the order has been placed")
        update.save()
        thank=True
        
        id = Order.order_id
        oid=str(id)+"Shopycart"
        param_dict={
            'MID':keys.MID,
            'ORDER_ID':oid,
            'TXN_AMOUNT':str(amount),
            'CUST_ID':email,
            'INDUSTRY_TYPE_ID':'Retail',
            'WEBSITE':'WEBSTAGING',
            'CHANNEL_ID':'WEB',
            'CALLBACK_URL':'http://127.0.0.1:8000/handlerequest/',
        }
        param_dict['CHECKSUMHASH']= Checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request, 'paytm.html',{'param_dict':param_dict})
         
    
    return render(request,'checkout.html')

@csrf_exempt
def handlerequest(request):
    form= request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i== 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY,checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print("order Successfull")
            a= response_dict["ORDERID"]
            b= response_dict['TXNAMOUNT']
            rid= a.replace("Shopycart","")
            
            print(rid)
            filter2= Orders.objects.filter(order_id=rid)
            print(filter2)
            print(a,b)
            for post1 in filter2:
                
                post1.oid = a
                post1.amountpaid=b
                post1.paymentstatus= "PAID"
                post1.save()
            print("run agede function")
        else:
            print("order was not successful because "+ response_dict['RESPMSG'])
    return render (request,'paymentstatus.html',{'response':response_dict})

def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login & try Again")
        return redirect('/auth/login')

    currentuser = request.user.username
    print(currentuser)

    items = Orders.objects.filter(email=currentuser)

    if items.exists():  # Check if there are any orders
        myid = items.last().order_id  # Get the last order_id
        status = OrderUpdate.objects.filter(order_id=int(myid))
    else:
        myid = None
        status = None  # No order updates

    context = {"items": items, "status": status}
    print(context)
    
    return render(request, "profile.html", context)


def termandcondition(request):
    return render(request,"term-and-condition.html")
def privacypolicy(request):
    return render(request,"privacy-policy.html")