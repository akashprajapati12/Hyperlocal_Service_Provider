import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hyperlocal_Service_Provider.settings')
django.setup()

from users.models import UserProfile
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking
from payments.models import Payment
from reviews.models import Review
from datetime import date, timedelta

def seed():
    print("Seeding database...")

    # Create admin
    admin, _ = UserProfile.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@hyperlocal.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    admin.set_password('admin123')
    admin.save()
    print("  Admin: admin / admin123")

    # Create customers
    customers = []
    for i, (fn, ln) in enumerate([('Rahul', 'Sharma'), ('Priya', 'Patel'), ('Amit', 'Kumar')], 1):
        u, _ = UserProfile.objects.get_or_create(
            username=f'customer{i}',
            defaults={'email': f'customer{i}@test.com', 'first_name': fn, 'last_name': ln, 'role': 'customer', 'phone': f'98765{i:05d}'}
        )
        u.set_password('test1234')
        u.save()
        customers.append(u)
    print("  Customers created (password: test1234)")

    # Create providers
    provider_data = [
        ('provider1', 'Suresh', 'Verma', 'Plumbing', 'Delhi', 'Experienced plumber with 10+ years.'),
        ('provider2', 'Meena', 'Devi', 'Electrical', 'Mumbai', 'Licensed electrician specializing in home wiring.'),
        ('provider3', 'Vikram', 'Singh', 'Cleaning', 'Bangalore', 'Professional cleaning services for homes and offices.'),
        ('provider4', 'Anita', 'Joshi', 'Tutoring', 'Pune', 'Mathematics tutor for classes 8-12.'),
        ('provider5', 'Rajesh', 'Nair', 'Beauty', 'Chennai', 'Hair stylist and beauty consultant.'),
    ]
    providers = []
    for uname, fn, ln, skill, loc, bio in provider_data:
        u, _ = UserProfile.objects.get_or_create(
            username=uname,
            defaults={'email': f'{uname}@test.com', 'first_name': fn, 'last_name': ln, 'role': 'provider', 'phone': '9876500001'}
        )
        u.set_password('test1234')
        u.save()
        sp, _ = ServiceProvider.objects.get_or_create(
            user=u, defaults={'skill': skill, 'location': loc, 'bio': bio, 'is_verified': True}
        )
        providers.append(sp)
    print("  Providers created (password: test1234)")

    # Create services
    services_data = [
        (providers[0], 'Pipe Repair', 'Fix leaking pipes and faucets.', 500, 'plumbing'),
        (providers[0], 'Bathroom Fitting', 'Complete bathroom plumbing installation.', 2500, 'plumbing'),
        (providers[1], 'Wiring Repair', 'Electrical wiring and switchboard repair.', 800, 'electrical'),
        (providers[1], 'Fan Installation', 'Ceiling fan installation and repair.', 400, 'electrical'),
        (providers[2], 'Deep Cleaning', 'Full house deep cleaning service.', 3000, 'cleaning'),
        (providers[2], 'Kitchen Cleaning', 'Thorough kitchen cleaning and degreasing.', 1500, 'cleaning'),
        (providers[3], 'Math Tutoring', 'One-on-one math tutoring for board exams.', 600, 'tutoring'),
        (providers[3], 'Science Tutoring', 'Physics and Chemistry tutoring.', 700, 'tutoring'),
        (providers[4], 'Haircut', 'Professional haircut at your doorstep.', 300, 'beauty'),
        (providers[4], 'Bridal Makeup', 'Complete bridal makeup package.', 5000, 'beauty'),
    ]
    services = []
    for prov, name, desc, price, cat in services_data:
        s, _ = Service.objects.get_or_create(
            provider=prov, service_name=name,
            defaults={'description': desc, 'price': price, 'category': cat}
        )
        services.append(s)
    print(f"  {len(services)} services created")

    # Create bookings
    for i, (cust, svc) in enumerate([
        (customers[0], services[0]),
        (customers[0], services[4]),
        (customers[1], services[2]),
        (customers[1], services[6]),
        (customers[2], services[8]),
    ]):
        status = ['pending', 'confirmed', 'completed', 'completed', 'pending'][i]
        b, created = Booking.objects.get_or_create(
            user=cust, service=svc,
            defaults={'provider': svc.provider, 'booking_date': date.today() + timedelta(days=i+1), 'status': status}
        )
        if created and status in ('completed',):
            Payment.objects.get_or_create(
                booking=b, defaults={'amount': svc.price, 'payment_method': 'online', 'payment_status': 'paid'}
            )
            Review.objects.get_or_create(
                user=cust, service=svc, booking=b,
                defaults={'rating': 4 + (i % 2), 'comment': 'Great service! Highly recommended.'}
            )
    print("  Bookings, payments, and reviews created")
    print("\nDone! You can now login with:")
    print("  Admin: admin / admin123")
    print("  Customer: customer1 / test1234")
    print("  Provider: provider1 / test1234")

if __name__ == '__main__':
    seed()
