from django.core.management.base import BaseCommand
from jobs.models import Country, Province, City, Barangay

class Command(BaseCommand):
    help = 'Creates initial location data for Surigao City'

    def handle(self, *args, **kwargs):
        # Create Philippines
        philippines, created = Country.objects.get_or_create(
            name='Philippines',
            code='PH'
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} Philippines'))

        # Create Surigao del Norte
        surigao_del_norte, created = Province.objects.get_or_create(
            country=philippines,
            name='Surigao del Norte',
            code='SUN'
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} Surigao del Norte'))

        # Create Surigao City
        surigao_city, created = City.objects.get_or_create(
            province=surigao_del_norte,
            name='Surigao City',
            code='SUR'
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} Surigao City'))

        # Create Barangays
        barangays = [
            'Alegria',
            'Ampayon',
            'Anomar',
            'Aurora',
            'Baan',
            'Bancasi',
            'Bilabid',
            'Bonifacio',
            'Buenavista',
            'Cabongbongan',
            'Cagniog',
            'Cantiasay',
            'Catadman',
            'Dagohoy',
            'Danao',
            'Day-asan',
            'De la Paz',
            'Doongan',
            'Gamut',
            'Ibabao',
            'Libuac',
            'Lipata',
            'Lisondra',
            'Luna',
            'Mabini',
            'Mabua',
            'Magallanes',
            'Magsaysay',
            'Mat-i',
            'Nonoc',
            'Orok',
            'Poctoy',
            'Punta Bilar',
            'Quezon',
            'Rizal',
            'Sabang',
            'San Isidro',
            'San Jose',
            'San Juan',
            'San Pedro',
            'San Roque',
            'Serna',
            'Sidlakan',
            'Silop',
            'Sugbay',
            'Sukailang',
            'Taft',
            'Talisay',
            'Togbongon',
            'Trinidad',
            'Washington'
        ]

        for barangay_name in barangays:
            barangay, created = Barangay.objects.get_or_create(
                city=surigao_city,
                name=barangay_name,
                code=barangay_name[:3].upper()
            )
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} Barangay {barangay_name}')) 