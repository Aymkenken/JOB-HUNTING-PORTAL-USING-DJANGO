from django.core.management.base import BaseCommand
from jobs.models import Country, Province, City, Barangay

class Command(BaseCommand):
    help = 'Populates the database with initial location data'

    def handle(self, *args, **options):
        # Create Philippines
        philippines, created = Country.objects.get_or_create(
            name="Philippines",
            code="PH"
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Philippines'))

        # Create Surigao del Norte
        surigao_norte, created = Province.objects.get_or_create(
            country=philippines,
            name="Surigao del Norte",
            code="SUN"
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Surigao del Norte'))

        # Create Surigao City
        surigao_city, created = City.objects.get_or_create(
            province=surigao_norte,
            name="Surigao City",
            code="SUR"
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Surigao City'))

        # Create barangays in Surigao City
        barangays = [
            "Alegria", "Anomar", "Aurora", "Balibayon", "Baybay", "Bilabid",
            "Bitaugan", "Bonifacio", "Buenavista", "Cabongbongan", "Cagniog",
            "Cantiasay", "Capalayan", "Catadman", "Danao", "Danawan", "Day-asan",
            "Ipil", "Libuac", "Lipata", "Lisondra", "Luna", "Mabini", "Mabua",
            "Manjagao", "Mapawa", "Mat-i", "Nonoc", "Orok", "Poctoy", "Punta Bilar",
            "Quezon", "Rizal", "Sabang", "San Isidro", "San Jose", "San Juan",
            "San Pedro", "San Roque", "Serna", "Sidlakan", "Sugbay", "Taft",
            "Taligaman", "Togbongon", "Trinidad", "Washington", "Zaragoza"
        ]

        created_count = 0
        for barangay_name in barangays:
            barangay, created = Barangay.objects.get_or_create(
                city=surigao_city,
                name=barangay_name,
                code=f"SUR-{barangay_name[:3].upper()}"
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} barangays in Surigao City')) 