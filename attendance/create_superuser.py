from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='MICHAEL',
        email='kingsmichael.x@gmail.com',
        password='MICHAEL123!'
    )
    print('Superuser created!')
