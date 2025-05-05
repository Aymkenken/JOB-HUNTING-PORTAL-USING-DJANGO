import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobpoint.settings')
django.setup()

from jobs.models import Country, Province, City, Barangay

def populate_locations():
    # Create Philippines
    philippines = Country.objects.create(
        name="Philippines",
        code="PH"
    )

    # Create Surigao del Norte
    surigao_norte = Province.objects.create(
        country=philippines,
        name="Surigao del Norte",
        code="SUN"
    )

    # Create Surigao City
    surigao_city = City.objects.create(
        province=surigao_norte,
        name="Surigao City",
        code="SUR"
    )

    # Create some barangays in Surigao City
    barangays = [
        "Alegria",
        "Anomar",
        "Aurora",
        "Balibayon",
        "Baybay",
        "Bilabid",
        "Bitaugan",
        "Bonifacio",
        "Buenavista",
        "Cabongbongan",
        "Cagniog",
        "Cantiasay",
        "Capalayan",
        "Catadman",
        "Danao",
        "Danawan",
        "Day-asan",
        "Ipil",
        "Libuac",
        "Lipata",
        "Lisondra",
        "Luna",
        "Mabini",
        "Mabua",
        "Manjagao",
        "Mapawa",
        "Mat-i",
        "Nonoc",
        "Orok",
        "Poctoy",
        "Punta Bilar",
        "Quezon",
        "Rizal",
        "Sabang",
        "San Isidro",
        "San Jose",
        "San Juan",
        "San Pedro",
        "San Roque",
        "Serna",
        "Sidlakan",
        "Sugbay",
        "Taft",
        "Taligaman",
        "Togbongon",
        "Trinidad",
        "Washington",
        "Zaragoza"
    ]

    for barangay_name in barangays:
        Barangay.objects.create(
            city=surigao_city,
            name=barangay_name,
            code=f"SUR-{barangay_name[:3].upper()}"
        )

if __name__ == '__main__':
    print("Populating locations...")
    populate_locations()
    print("Done!") 