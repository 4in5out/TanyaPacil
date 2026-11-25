from django.core.management.base import BaseCommand

from apps.resources.models import Resource, ResourceCategory


class Command(BaseCommand):
    help = 'Seed starter Fasilkom UI (DDP1) coding resources for Pak Chill.'

    def handle(self, *args, **options):
        cat_python, _ = ResourceCategory.objects.get_or_create(
            name='DDP1 Python Basics',
            defaults={'icon': '🐍', 'description': 'Core Python fundamentals for DDP1'},
        )
        cat_tools, _ = ResourceCategory.objects.get_or_create(
            name='Tools & GitLab Pacil',
            defaults={'icon': '🛠️', 'description': 'Git, GitLab Fasilkom, and IDE workflows'},
        )
        cat_external, _ = ResourceCategory.objects.get_or_create(
            name='External References (GFG & W3S)',
            defaults={'icon': '🌐', 'description': 'Curated GeeksforGeeks & W3Schools guides'},
        )

        starter_resources = [
            {
                'title': 'DDP1 Module — Python Collections (List, Tuple, Set, Dict)',
                'category': cat_python,
                'resource_type': Resource.TYPE_NOTE,
                'summary': 'Comparison of mutable vs immutable Python collections with usage examples.',
                'extracted_text': (
                    'Python Built-in Data Structures:\n'
                    '1. List ([1, 2, 3]): Ordered, mutable, allows duplicates. Use append(), pop(), slicing.\n'
                    '2. Tuple ((1, 2, 3)): Ordered, immutable, allows duplicates. Faster and safe for fixed data or dict keys.\n'
                    '3. Set ({1, 2, 3}): Unordered, mutable, NO duplicates. Great for membership tests (x in s) and union/intersection.\n'
                    '4. Dictionary ({"nim": "2406...", "nama": "Budi"}): Key-value pairs, keys must be immutable and unique. '
                    'Use .get(key, default) to avoid KeyError.\n'
                    'Common Pitfall: IndexError occurs when accessing a list index >= len(list) or < -len(list).'
                ),
            },
            {
                'title': 'DDP1 Module — Functions & Recursion Essentials',
                'category': cat_python,
                'resource_type': Resource.TYPE_NOTE,
                'summary': 'Base cases, recursive cases, and preventing RecursionError in Python.',
                'extracted_text': (
                    'Recursion is when a function calls itself to solve a smaller subproblem.\n'
                    'Every valid recursive function needs TWO parts:\n'
                    '1. Base Case: Stops the recursion (e.g., if n <= 1: return 1).\n'
                    '2. Recursive Case: Moves closer to the base case (e.g., return n * factorial(n - 1)).\n'
                    'Common Pitfall: Forgetting the base case or not shrinking the input causes RecursionError '
                    '(maximum recursion depth exceeded, default ~1000 in Python).'
                ),
            },
            {
                'title': 'Panduan Git & GitLab Fasilkom UI (Pacil)',
                'category': cat_tools,
                'resource_type': Resource.TYPE_NOTE,
                'summary': 'Basic Git workflow (clone, status, add, commit, push) for DDP1 labs and assignments.',
                'extracted_text': (
                    'Standard GitLab Pacil workflow for DDP1 assignments:\n'
                    '1. Clone repository: git clone <repo_url>\n'
                    '2. Check changed files: git status\n'
                    '3. Stage changes: git add <filename> or git add .\n'
                    '4. Commit with a clear message: git commit -m "Implement lab 3 solution"\n'
                    '5. Push to remote: git push origin main\n'
                    'Tip: Pull first (git pull) when working in a team to avoid merge conflicts.'
                ),
            },
            {
                'title': 'W3Schools — Python Exceptions & Debugging Reference',
                'category': cat_external,
                'resource_type': Resource.TYPE_EXTERNAL,
                'source_url': 'https://www.w3schools.com/python/python_try_except.asp',
                'summary': 'Quick guide to try/except/finally and common Python error types.',
                'extracted_text': (
                    'W3Schools Python Try...Except Summary:\n'
                    '- try: lets you test a block of code for errors.\n'
                    '- except: lets you handle specific errors like ValueError, ZeroDivisionError, IndexError, KeyError, TypeError.\n'
                    '- else: runs if no errors were raised.\n'
                    '- finally: always runs regardless of whether an exception occurred (useful for closing files).'
                ),
            },
            {
                'title': 'GeeksforGeeks — Python OOP (Classes & Objects)',
                'category': cat_external,
                'resource_type': Resource.TYPE_EXTERNAL,
                'source_url': 'https://www.geeksforgeeks.org/python-oops-concepts/',
                'summary': 'Overview of classes, __init__, self, inheritance, and encapsulation in Python.',
                'extracted_text': (
                    'GeeksforGeeks Python OOP Concepts:\n'
                    '- Class: A blueprint for creating objects (defined with class ClassName:).\n'
                    '- Object: An instance of a class holding state (attributes) and behavior (methods).\n'
                    '- __init__(self, ...): Constructor method called automatically when creating an instance.\n'
                    '- Inheritance: A child class inherits attributes and methods from a parent class using class Child(Parent): '
                    'and super().__init__(...).\n'
                    '- Encapsulation: Grouping data and methods, using _protected or __private naming conventions.'
                ),
            },
        ]

        created_count = 0
        for item in starter_resources:
            _, created = Resource.objects.get_or_create(
                title=item['title'],
                defaults=item,
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Seeded {created_count} new starter resource(s). Total active: {Resource.objects.filter(is_active=True).count()}')
        )
