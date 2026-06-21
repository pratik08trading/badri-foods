from .models import CartItem

def cart_count(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    count = CartItem.objects.filter(session_key=session_key).count()
    return {'cart_count': count}
