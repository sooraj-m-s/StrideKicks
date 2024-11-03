from .models import Users


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = {
        'email': details.get('email'),
        'first_name': details.get('first_name'),
        'last_name': details.get('last_name'),
    }

    if not fields['email']:
        return

    user = Users.objects.filter(email=fields['email']).first()
    if user:
        return {'is_new': False}

    user = Users(
        email=fields['email'],
        first_name=fields['first_name'],
        last_name=fields['last_name'],
        status='Active'
    )
    user.set_unusable_password()
    user.save()

    return {
        'is_new': True,
        'user': user
    }
