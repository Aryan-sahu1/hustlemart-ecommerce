from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from ecommerceapp.models import Contact, Product, Orders, OrderUpdate
from ecommerceapp import keys
from PayTm import Checksum
from math import ceil
import razorpay
from itertools import groupby

# Set Merchant Key
MERCHANT_KEY = keys.RAZORPAY_KEY_SECRET

# Home Page (Index)
def index(request):
    catProds = Product.objects.values('category', 'id')
    categories = {item['category'] for item in catProds}
    
    all_products = Product.objects.all().order_by('category')
    grouped_products = {cat: list(prod) for cat, prod in groupby(all_products, lambda x: x.category)}

    allProds = [
        [grouped_products[cat], range(1, ceil(len(grouped_products[cat]) / 4)), ceil(len(grouped_products[cat]) / 4)]
        for cat in categories
    ]
    
    return render(request, 'index.html', {'allProds': allProds})


# About Page
def about(request):
    return render(request, 'about.html')


# Contact Page
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        desc = request.POST.get("desc")
        phonen = request.POST.get("phonen")

        if name and email and desc and phonen:  # Basic validation
            myquery = Contact(name=name, email=email, desc=desc, phonenumber=phonen)
            myquery.save()
            messages.success(request, "We will get back to you soon!")
            return redirect("contact")
        else:
            messages.error(request, "All fields are required!")

    return render(request, 'contact.html')


# Checkout Page with Razorpay Integration
def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login & try Again")
        return redirect('/auth/login')

    if request.method == "POST":
        try:
            items_json = request.POST.get('itemsJson', '')    
            name = request.POST.get('name', '')    
            amount = int(float(request.POST.get('amt', '0')) * 100)  # Convert to paisa with default 0    
            email = request.POST.get('email', '')    
            address1 = request.POST.get('address1', '')    
            address2 = request.POST.get('address2', '')    
            city = request.POST.get('city', '')    
            state = request.POST.get('state', '')    
            zip_code = request.POST.get('zip_code', '')    
            phone = request.POST.get('phone', '')    

            if not name or not email or amount <= 0:
                messages.error(request, "Invalid input data!")
                return redirect("checkout")

            order = Orders(
                items_json=items_json, name=name, email=email, amount=amount / 100,
                address1=address1, address2=address2, city=city, state=state, zip_code=zip_code, phone=phone
            ) 
            order.save()
            update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
            update.save()

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1"
            })

            order.oid = razorpay_order['id']
            order.save()

            return render(request, 'razorpay_checkout.html', {
                'order': order, 
                'razorpay_order': razorpay_order, 
                'razorpay_key': settings.RAZORPAY_KEY_ID
            })

        except ValueError:
            messages.error(request, "Invalid amount entered!")
            return redirect("checkout")

    return render(request, 'checkout.html')



# Razorpay Payment Handling
@csrf_exempt
def handlerequest(request):
    form = request.POST
    response_dict = {}

    for key in form.keys():
        response_dict[key] = form[key]
        if key == 'CHECKSUMHASH':
            checksum = form[key]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)

    if verify:
        order_id = response_dict.get("ORDERID", "")
        amount_paid = response_dict.get('TXNAMOUNT', 0)
        rid = order_id.replace("Shopycart", "")

        # Fetch order from database
        filter_orders = Orders.objects.filter(order_id=rid)

        if response_dict['RESPCODE'] == '01':  # Payment success
            for order in filter_orders:
                order.oid = order_id
                order.amountpaid = amount_paid
                order.paymentstatus = "PAID"
                order.save()
            messages.success(request, "Payment successful! Your order has been placed.")
        else:  # Payment failed
            for order in filter_orders:
                order.paymentstatus = "UNPAID"
                order.save()
            messages.error(request, f"Payment failed: {response_dict['RESPMSG']}")

    return render(request, 'paymentstatus.html', {'response': response_dict})


# User Profile Page (Order Tracking)
def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Login & try Again")
        return redirect('/auth/login')

    current_user = request.user.username
    items = Orders.objects.filter(email=current_user)

    last_order_id = items.last().order_id if items.exists() else None
    status = OrderUpdate.objects.filter(order_id=int(last_order_id)) if last_order_id else None

    return render(request, "profile.html", {"items": items, "status": status})


# Terms and Conditions Page
def termandcondition(request):
    return render(request, "term-and-condition.html")


# Privacy Policy Page
def privacypolicy(request):
    return render(request, "privacy-policy.html")
