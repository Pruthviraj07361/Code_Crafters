# accounts/management/commands/bootstrap_superuser.py
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import AdminProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates (or promotes) an AdminProfile with staff_type=superuser, for initial setup only.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--name', default='Superuser')
        parser.add_argument('--phone', default='0000000000')

    def handle(self, *args, **options):
        email = options['email']
        user, created = User.objects.get_or_create(
            username=email, defaults={'email': email},
        )
        if created:
            user.set_password(options['password'])
            user.save()
            self.stdout.write(f'Created user {email}')
        else:
            self.stdout.write(f'User {email} already exists, promoting instead')

        profile, _ = AdminProfile.objects.get_or_create(
            user=user,
            defaults={'name': options['name'], 'phone': options['phone']},
        )
        profile.staff_type = AdminProfile.STAFF_SUPERUSER
        profile.is_approved = True
        profile.save(update_fields=['staff_type', 'is_approved'])

        self.stdout.write(self.style.SUCCESS(f'{email} is now a superuser.'))