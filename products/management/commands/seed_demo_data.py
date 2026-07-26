from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product
from jobs.models import JobPosting

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with demo categories, a demo seller, demo products, and job postings."

    def handle(self, *args, **options):
        # --- Demo seller account ---
        seller, created = User.objects.get_or_create(
            username='demo_seller',
            defaults={
                'email': 'seller@corazon.com',
                'is_seller': True,
                'store_name': 'Corazon Official Store',
            }
        )
        if created:
            seller.set_password('sellerpass123')
            seller.save()
            self.stdout.write(self.style.SUCCESS("Created demo seller: demo_seller / sellerpass123"))

        # --- Categories ---
        categories_data = [
            ('Electronics', '💻'),
            ('Home & Kitchen', '🏠'),
            ('Fashion', '👗'),
            ('Books', '📚'),
            ('Sports & Outdoors', '⚽'),
            ('Beauty & Health', '💄'),
        ]
        categories = {}
        for name, icon in categories_data:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon})
            categories[name] = cat

        # --- Products ---
        products_data = [
            ('Wireless Bluetooth Headphones', 'Electronics', 45000, 36000, 25,
             'Over-ear wireless headphones with noise cancellation and 30-hour battery life.'),
            ('4K Ultra HD Smart TV 55"', 'Electronics', 480000, None, 10,
             'Crisp 4K resolution with built-in streaming apps and voice remote.'),
            ('Smartphone 128GB', 'Electronics', 320000, 289000, 18,
             '6.5" display, dual camera, all-day battery life.'),
            ('Bluetooth Portable Speaker', 'Electronics', 28000, None, 40,
             'Compact speaker with rich bass and 12-hour playtime.'),
            ('Stainless Steel Cookware Set', 'Home & Kitchen', 95000, 78000, 15,
             '10-piece cookware set, dishwasher safe, oven safe up to 260°C.'),
            ('Robot Vacuum Cleaner', 'Home & Kitchen', 165000, None, 20,
             'Smart navigation robot vacuum with app control and auto-charging dock.'),
            ('Standing Fan 18-inch', 'Home & Kitchen', 32000, 27000, 22,
             'Powerful 3-speed standing fan with wide oscillation.'),
            ("Men's Classic Denim Jacket", 'Fashion', 22000, 17500, 40,
             'Timeless denim jacket, available in multiple sizes, 100% cotton.'),
            ("Women's Running Shoes", 'Fashion', 26000, None, 30,
             'Lightweight breathable running shoes with cushioned sole.'),
            ('Ankara Print Shirt', 'Fashion', 15000, 12000, 35,
             'Vibrant Ankara print shirt, tailored fit, breathable fabric.'),
            ('The Art of Programming', 'Books', 12000, None, 50,
             'A comprehensive guide to writing clean, maintainable code.'),
            ('Mystery at Midnight (Novel)', 'Books', 6500, 4900, 60,
             'A gripping mystery novel that will keep you guessing until the last page.'),
            ('Personal Finance 101', 'Books', 8500, None, 44,
             'A practical guide to budgeting, saving, and building wealth.'),
            ('Yoga Mat with Carry Strap', 'Sports & Outdoors', 9500, None, 45,
             'Non-slip eco-friendly yoga mat, 6mm thick, includes carry strap.'),
            ('Adjustable Dumbbell Set', 'Sports & Outdoors', 78000, 65000, 12,
             'Space-saving adjustable dumbbells, 5-50 lbs per hand.'),
            ('Football (Size 5)', 'Sports & Outdoors', 11000, 8900, 33,
             'Match-quality size 5 football, durable synthetic leather.'),
            ('Vitamin C Serum', 'Beauty & Health', 9800, None, 70,
             'Brightening facial serum with hyaluronic acid, for all skin types.'),
            ('Electric Toothbrush', 'Beauty & Health', 19500, 15900, 35,
             'Rechargeable electric toothbrush with 3 cleaning modes.'),
            ('Shea Butter Body Cream', 'Beauty & Health', 6000, None, 58,
             'Deeply moisturizing body cream made with natural shea butter.'),
        ]

        created_count = 0
        for name, cat_name, price, discount, stock, desc in products_data:
            _, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'seller': seller,
                    'category': categories[cat_name],
                    'price': price,
                    'discount_price': discount,
                    'stock': stock,
                    'description': desc,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} demo products."))
        self.stdout.write(self.style.SUCCESS(
            f"({Product.objects.filter(is_active=True).count()} active products total — "
            "with 12 per page, that's enough to see pagination in action on the homepage.)"
        ))

        # --- Job postings ---
        jobs_data = [
            ('Backend Django Developer', 'Engineering', 'Remote', 'full_time',
             'Build and maintain scalable backend services for our marketplace platform using Django.',
             '3+ years Python/Django experience. Familiarity with REST APIs and PostgreSQL.',
             600000, 950000, 'month', 'Monday - Friday', '9:00 AM - 5:00 PM'),
            ('Warehouse Associate', 'Operations', 'Lagos, Nigeria', 'full_time',
             'Pick, pack, and ship customer orders accurately and efficiently in our fulfillment center.',
             'Ability to lift 25kg. Prior warehouse experience a plus.',
             120000, 150000, 'month', 'Monday - Saturday', '8:00 AM - 6:00 PM'),
            ('Customer Support Specialist', 'Customer Service', 'Remote', 'part_time',
             'Help customers with order inquiries, returns, and general support via chat and email.',
             'Excellent written communication skills. Prior customer service experience preferred.',
             90000, 130000, 'month', 'Monday - Friday', '12:00 PM - 6:00 PM'),
            ('Marketing Intern', 'Marketing', 'Abuja, Nigeria', 'internship',
             'Assist the marketing team with social media campaigns, content creation, and analytics.',
             'Currently pursuing a degree in Marketing, Communications, or related field.',
             None, 80000, 'month', 'Monday - Friday', '9:00 AM - 3:00 PM'),
        ]
        job_created = 0
        for title, dept, location, jtype, desc, reqs, sal_min, sal_max, sal_period, work_days, work_hours in jobs_data:
            _, created = JobPosting.objects.get_or_create(
                title=title,
                defaults={
                    'department': dept, 'location': location, 'job_type': jtype,
                    'description': desc, 'requirements': reqs, 'is_active': True,
                    'salary_min': sal_min, 'salary_max': sal_max, 'salary_period': sal_period,
                    'work_days': work_days, 'work_hours': work_hours,
                }
            )
            if created:
                job_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {job_created} demo job postings."))
        self.stdout.write(self.style.SUCCESS("Demo data seeding complete!"))
