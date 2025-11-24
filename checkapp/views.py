from django.shortcuts import render, get_object_or_404,redirect
from .models import Product
from .models import CartItem


# Create your views here.


def product_list(request):
    All_data = Product.objects.all()
    return render(request, 'productpage.html', {'All_data': All_data})

def single_product(request, product_id):
    single_data = get_object_or_404(Product,id=product_id)
    return render(request, 'singleproduct.html', {'single_data':single_data })



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(cartproduct=product)
    if created:
        cart_item.quantity = 1  
    else:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_view')



def cart_view(request):
    cart_items = CartItem.objects.all()
    total_amount = sum(item.total_cost for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_amount': total_amount})


def cart_update(request, cart_id):
    cart_item = get_object_or_404(CartItem, id=cart_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if  quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart_view')

def remove_cart(request,cart_id):
    cart_item=get_object_or_404(CartItem, id=cart_id)
    cart_item.delete()
    return redirect('cart_view')






from .forms import BillingDetailsForm

def checkout(request):
    cart_items = CartItem.objects.all()
    total_price = sum(item.cartproduct.price * item.quantity for item in cart_items)


    if request.method == 'POST':
        form = BillingDetailsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_confirmation')
        
    else:
        form = BillingDetailsForm()


    context = {
        'cart_items': cart_items,    
        'total_price': total_price,
        'form': form,
    }
    return render(request, 'checkout.html', context)

from  django.shortcuts import render
from .models import CartItem,BillingDetails


# def order_confirmation(request):

#     delivery = BillingDetails.objects.last()
#     cart_items = CartItem.objects.all() 
#     total_price = sum(item.product.price * item.quantity for item in cart_items)



#     context = {
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'delivery': delivery,
#     }


#     return render(request, 'checkout.html', context)



