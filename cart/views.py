from django.shortcuts import get_object_or_404, redirect, render
from app.models import Home
from .models import Cart, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
import razorpay 
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


from app.models import Home
from .models import Cart, CartItem, Order, OrderItem, Payment

# Create your views here.

print(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET)
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))


def get_cart(user):
    print(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET)

    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart(request):
    cart = get_cart(request.user)
    items = cart.items.select_related("product")

    total = sum(item.product.price * item.quantity for item in items)
    print(total)
    context = {
        "cart": cart,
        "items": items,
        "total": total,
    }
    return render(request, "cart.html", context)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Home, id=product_id)
    cart = get_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    return redirect("cart")


def increase_quantity(request, item_id):

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    item.quantity += 1
    item.save()

    return redirect("cart")


def decrease_quantity(request, item_id):

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect("cart")


def remove_from_cart(request, item_id):

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    item.delete()
    return redirect("cart")


def cancel_order_and_restore_stock(order):
    """Cancel an unpaid order and put its stock back. Safe to call twice."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.staus != "PENDING_PAYMENT":
            return
        for item in order.items.all():
            Home.objects.filter(pk=item.product_id).update(
                stock=F("stock") + item.quantity
            )
        order.staus = "CANCELLED"
        order.save()


@login_required
def place_order(request):
    cart = get_cart(request.user)
    items = cart.items.select_related("product")

    if not items:
        return redirect("cart")

    total = sum(i.product.price * i.quantity for i in items)

    if request.method != "POST":
        return render(request, "place_order.html", {"items": items, "total": total})

    method = request.POST.get("payment_method", "COD")

    # Drop any earlier unpaid order so stock isn't reserved twice
    for old in Order.objects.filter(user=request.user, staus="PENDING_PAYMENT"):
        cancel_order_and_restore_stock(old)

    with transaction.atomic():
        locked = {
            p.id: p
            for p in Home.objects.select_for_update().filter(
                id__in=[i.product_id for i in items]
            )
        }
        for i in items:
            p = locked[i.product_id]
            if not p.is_available or p.stock < i.quantity:
                messages.error(request, f"Sorry, {p.name} doesn't have enough stock.")
                return redirect("cart")

        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            staus="PENDING_PAYMENT" if method == "RAZORPAY" else "PLACED",
            full_name=request.POST["full_name"],
            phone=request.POST["phone"],
            address=request.POST["address"],
            city=request.POST["city"],
            state=request.POST["state"],
            pincode=request.POST["pincode"],
            payment_method=method,
        )

        for i in items:
            OrderItem.objects.create(
                order=order,
                product=i.product,
                quantity=i.quantity,
                price=i.product.price,
            )
            p = locked[i.product_id]
            p.stock -= i.quantity
            p.save()

        if method == "RAZORPAY":
            rp_order = client.order.create({
                "amount": int(total * 100),   # paise
                "currency": "INR",
                "receipt": f"order_{order.id}",
            })
            Payment.objects.create(
                order=order,
                razorpay_order_id=rp_order["id"],
                amount=total,
            )
        else:
            cart.items.all().delete()   # COD: done

    if method == "RAZORPAY":
        return redirect("payment", order_id=order.id)

    messages.success(request, "Order placed successfully!")
    return redirect("orders")


@login_required
def payment(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, user=request.user, staus="PENDING_PAYMENT"
    )
    context = {
        "order": order,
        "payment": order.payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount_paise": int(order.total_amount * 100),
    }
    return render(request, "payment.html", context)


@login_required
@require_POST
def payment_verify(request):
    rp_order_id = request.POST.get("razorpay_order_id", "")
    rp_payment_id = request.POST.get("razorpay_payment_id", "")
    rp_signature = request.POST.get("razorpay_signature", "")

    pay = get_object_or_404(
        Payment.objects.select_related("order"),
        razorpay_order_id=rp_order_id,
        order__user=request.user,
    )
    order = pay.order

    if pay.status == "PAID":  # double submit / refresh
        return redirect("orders")

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": rp_order_id,
                "razorpay_payment_id": rp_payment_id,
                "razorpay_signature": rp_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        pay.status = "FAILED"
        pay.save()
        cancel_order_and_restore_stock(order)
        messages.error(request, "Payment verification failed. Please try again.")
        return redirect("cart")

    pay.razorpay_payment_id = rp_payment_id
    pay.razorpay_signature = rp_signature
    pay.status = "PAID"
    pay.save()

    order.staus = "PLACED"
    order.save()

    get_cart(request.user).items.all().delete()

    messages.success(request, "Payment successful! Your order is placed.")
    return redirect("orders")


@login_required
def cancel_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    cancel_order_and_restore_stock(order)
    messages.info(request, "Order cancelled. Your cart is unchanged.")
    return redirect("cart")


def order_view(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    return render(request, "orders.html", {"orders": orders})
