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
            ('Wireless Bluetooth Headphones', 'Electronics', 49.99, 39.99, 25,
             'Over-ear wireless headphones with noise cancellation and 30-hour battery life.'),
            ('4K Ultra HD Smart TV 55"', 'Electronics', 499.99, None, 10,
             'Crisp 4K resolution with built-in streaming apps and voice remote.'),
            ('Stainless Steel Cookware Set', 'Home & Kitchen', 129.99, 99.99, 15,
             '10-piece cookware set, dishwasher safe, oven safe up to 500°F.'),
            ('Robot Vacuum Cleaner', 'Home & Kitchen', 199.99, None, 20,
             'Smart navigation robot vacuum with app control and auto-charging dock.'),
            ("Men's Classic Denim Jacket", 'Fashion', 59.99, 44.99, 40,
             'Timeless denim jacket, available in multiple sizes, 100% cotton.'),
            ("Women's Running Shoes", 'Fashion', 79.99, None, 30,
             'Lightweight breathable running shoes with cushioned sole.'),
            ('The Art of Programming', 'Books', 34.99, None, 50,
             'A comprehensive guide to writing clean, maintainable code.'),
            ('Mystery at Midnight (Novel)', 'Books', 14.99, 9.99, 60,
             'A gripping mystery novel that will keep you guessing until the last page.'),
            ('Yoga Mat with Carry Strap', 'Sports & Outdoors', 24.99, None, 45,
             'Non-slip eco-friendly yoga mat, 6mm thick, includes carry strap.'),
            ('Adjustable Dumbbell Set', 'Sports & Outdoors', 149.99, 119.99, 12,
             'Space-saving adjustable dumbbells, 5-50 lbs per hand.'),
            ('Vitamin C Serum', 'Beauty & Health', 19.99, None, 70,
             'Brightening facial serum with hyaluronic acid, for all skin types.'),
            ('Electric Toothbrush', 'Beauty & Health', 39.99, 29.99, 35,
             'Rechargeable electric toothbrush with 3 cleaning modes.'),
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

        # --- Job postings ---
        jobs_data = [
            ('Backend Django Developer', 'Engineering', 'Remote', 'full_time',
             'Build and maintain scalable backend services for our marketplace platform using Django.',
             '3+ years Python/Django experience. Familiarity with REST APIs and PostgreSQL.'),
            ('Warehouse Associate', 'Operations', 'Chicago, IL', 'full_time',
             'Pick, pack, and ship customer orders accurately and efficiently in our fulfillment center.',
             'Ability to lift 50 lbs. Prior warehouse experience a plus.'),
            ('Customer Support Specialist', 'Customer Service', 'Remote', 'part_time',
             'Help customers with order inquiries, returns, and general support via chat and email.',
             'Excellent written communication skills. Prior customer service experience preferred.'),
            ('Marketing Intern', 'Marketing', 'New York, NY', 'internship',
             'Assist the marketing team with social media campaigns, content creation, and analytics.',
             'Currently pursuing a degree in Marketing, Communications, or related field.'),
        ]
        job_created = 0
        for title, dept, location, jtype, desc, reqs in jobs_data:
            _, created = JobPosting.objects.get_or_create(
                title=title,
                defaults={
                    'department': dept, 'location': location, 'job_type': jtype,
                    'description': desc, 'requirements': reqs, 'is_active': True,
                }
            )
            if created:
                job_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {job_created} demo job postings."))
        self.stdout.write(self.style.SUCCESS("Demo data seeding complete!"))
