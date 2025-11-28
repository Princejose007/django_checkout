from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.urls import reverse   # ✅ NEW
from django.contrib.auth.models import User

import razorpay

from .models import Product, CartItem, BillingDetails, Order, OrderItem
from .forms import BillingDetailsForm


# --- Product listing / detail ---

def product_list(request):
    All_data = Product.objects.all()
    return render(request, 'productpage.html', {'All_data': All_data})


def single_product(request, product_id):
    single_data = get_object_or_404(Product, id=product_id)
    return render(request, 'singleproduct.html', {'single_data': single_data})


# --- Cart operations ---

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, CartItem

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        cartproduct=product
    )

    if created:
        cart_item.quantity = 1
    else:
        cart_item.quantity += 1

    cart_item.save()
    return redirect('cart_view')


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_amount = sum(item.cartproduct.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })


@login_required
def cart_update(request, cart_id):
    cart_item = get_object_or_404(CartItem, id=cart_id, user=request.user)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart_view')


@login_required
def remove_cart(request, cart_id):
    cart_item = get_object_or_404(CartItem, id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('cart_view')


# --- Checkout & billing ---

from django.contrib.auth.decorators import login_required

@login_required
def checkout(request):
    # ✅ Always filter cart by logged-in user
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.cartproduct.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        form = BillingDetailsForm(request.POST)
        if form.is_valid():
            # 1) Save billing details & attach user
            billing_details = form.save(commit=False)
            billing_details.user = request.user
            billing_details.save()

            # 2) Recalculate totals from THIS user's cart
            cart_items = CartItem.objects.filter(user=request.user)
            if not cart_items.exists():
                return redirect('cart_view')

            total_quantity = sum(item.quantity for item in cart_items)
            total_price = sum(item.cartproduct.price * item.quantity for item in cart_items)

            # 3) Create Order (linked to billing + user)
            order = Order.objects.create(
                user=request.user,                # ✅ IMPORTANT
                billing_details=billing_details,
                total_price=total_price,
                total_quantity=total_quantity,
                status="Pending"
            )

            # 4) Create OrderItem(s) from CartItem(s)
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.cartproduct,
                    quantity=item.quantity,
                    price=item.cartproduct.price,
                )

            # (optional) clear cart after order
            # cart_items.delete()

            return redirect('order_confirmation')
    else:
        form = BillingDetailsForm()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'form': form,
    }
    return render(request, 'checkout.html', context)


# --- Order confirmation (Razorpay order creation) ---

def order_confirmation(request):
    # Last created order
    order = Order.objects.last()

    if not order:
        return redirect('cart_view')

    order_items = order.items.all()  # from related_name='items' in OrderItem

    # Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Razorpay works in paise
    amount_paise = int(order.total_price * 100)

    # Create Razorpay order
    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,  # Auto capture
    })

    # ✅ Build FULL absolute callback URL for Razorpay
    callback_url = request.build_absolute_uri(
        reverse('payment_success') + f'?order_id={order.id}'
    )

    context = {
        'order': order,
        'order_items': order_items,
        'delivery': order.billing_details,
        'total_price': order.total_price,

        # Razorpay related
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_amount': amount_paise,
        'callback_url': callback_url,  # ✅ send to template
    }
    return render(request, 'order_confirmation.html', context)


# --- Payment success callback (Razorpay -> this URL) ---

@csrf_exempt
def payment_success(request):
    """
    Razorpay will POST to this URL after payment with:
    - razorpay_payment_id
    - razorpay_order_id
    - razorpay_signature
    We verify signature and then mark order as Paid.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    order_id = request.GET.get('order_id')  # we send this in callback_url

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature and order_id):
        return HttpResponseBadRequest("Missing parameters")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        # Verify the signature from Razorpay
        client.utility.verify_payment_signature(params_dict)
        payment_ok = True
    except razorpay.errors.SignatureVerificationError:
        payment_ok = False

    order = get_object_or_404(Order, id=order_id)

    if payment_ok:
        order.status = "Paid"
        order.save()
        return render(request, 'payment_success.html', {"order": order})
    else:
        order.status = "Payment Failed"
        order.save()
        return render(request, 'payment_failed.html', {"order": order})
    






from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import userprofile







def register_view(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname', '')
        phone = request.POST.get('phone', '') 
        address = request.POST.get('address', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm-password', '')  # match your HTML name

        if not fullname or not phone or not email or not password or not confirm_password:
            messages.error(request, 'All fields are required')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=email).exists():
            messages.error(request, 'Email already exists')
        else:
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = fullname
            user.save()


            userprofile.objects.create(
            user=user,
            phone=phone,
            address=address
        )
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('product_list')

    return render(request, 'register.html')




def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('product_list')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


from django.contrib.auth import logout
def log_out_view(request):
    logout(request)
    return redirect('login_view')




from django.contrib.auth.decorators import login_required

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'order_history.html', {'orders': orders})
