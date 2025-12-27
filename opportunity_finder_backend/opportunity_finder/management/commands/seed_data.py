"""
Django management command to seed the database with initial data.

This command creates:
1. Taxonomy hierarchy (Opportunity Types -> Domains -> Specializations)
2. Locations hierarchy (Countries -> Cities)
3. User profiles with diverse backgrounds for testing matching
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from opportunities.models import (
    OpportunityType, Domain, Specialization, Location, Source
)
from profiles.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial taxonomy, locations, and user profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting existing data...')
            self._reset_data()

        self.stdout.write('Seeding sources...')
        self._seed_sources()

        self.stdout.write('Seeding taxonomy...')
        self._seed_taxonomy()

        self.stdout.write('Seeding locations...')
        self._seed_locations()

        self.stdout.write('Seeding user profiles...')
        self._seed_user_profiles()

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database!')
        )

    def _reset_data(self):
        """Reset existing data"""
        UserProfile.objects.all().delete()
        # Don't delete superuser, just profiles
        User.objects.exclude(is_superuser=True).delete()
        Specialization.objects.all().delete()
        Domain.objects.all().delete()
        OpportunityType.objects.all().delete()
        Location.objects.all().delete()
        Source.objects.all().delete()

    def _seed_sources(self):
        """Seed Telegram sources for ingestion"""

        sources_data = [
            {
                'name': 'Bright Scholarship Telegram',
                'source_type': Source.SourceType.TELEGRAM,
                'identifier': '@BrightScholarship',
                'enabled': True,
                'poll_interval_minutes': 10,
            },
            {
                'name': 'Afriwork English Telegram Channel',
                'source_type': Source.SourceType.TELEGRAM,
                'identifier': '@freelance_ethio',
                'enabled': True,
                'poll_interval_minutes': 10,
            },
            {
                'name': 'Ethio Jobs English Telegram Channel',
                'source_type': Source.SourceType.TELEGRAM,
                'identifier': '@ethiojobsofficial',
                'enabled': True,
                'poll_interval_minutes': 10,
            },
        ]

        created_sources = []
        for source_data in sources_data:
            source, created = Source.objects.get_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            if created:
                self.stdout.write(f'  Created source: {source.name}')
            else:
                self.stdout.write(f'  Source already exists: {source.name}')
            created_sources.append(source)

        self.stdout.write(f'Created {len(created_sources)} sources')

    def _seed_taxonomy(self):
        """Seed the complete taxonomy hierarchy"""

        # Opportunity Types
        job_type, _ = OpportunityType.objects.get_or_create(name='JOB')
        scholarship_type, _ = OpportunityType.objects.get_or_create(name='SCHOLARSHIP')
        internship_type, _ = OpportunityType.objects.get_or_create(name='INTERNSHIP')
        training_type, _ = OpportunityType.objects.get_or_create(name='TRAINING')

        # Job Domains
        software_domain, _ = Domain.objects.get_or_create(
            name='Software', opportunity_type=job_type
        )
        data_science_domain, _ = Domain.objects.get_or_create(
            name='Data Science', opportunity_type=job_type
        )
        engineering_domain, _ = Domain.objects.get_or_create(
            name='Engineering', opportunity_type=job_type
        )
        healthcare_domain, _ = Domain.objects.get_or_create(
            name='Healthcare', opportunity_type=job_type
        )
        education_domain, _ = Domain.objects.get_or_create(
            name='Education', opportunity_type=job_type
        )
        marketing_domain, _ = Domain.objects.get_or_create(
            name='Marketing', opportunity_type=job_type
        )
        design_domain, _ = Domain.objects.get_or_create(
            name='Design', opportunity_type=job_type
        )
        finance_domain, _ = Domain.objects.get_or_create(
            name='Finance', opportunity_type=job_type
        )

        # Scholarship Domains
        masters_domain, _ = Domain.objects.get_or_create(
            name='Masters', opportunity_type=scholarship_type
        )
        phd_domain, _ = Domain.objects.get_or_create(
            name='PhD', opportunity_type=scholarship_type
        )
        bachelors_domain, _ = Domain.objects.get_or_create(
            name='Bachelors', opportunity_type=scholarship_type
        )
        undergraduate_domain, _ = Domain.objects.get_or_create(
            name='Undergraduate', opportunity_type=scholarship_type
        )
        postgraduate_domain, _ = Domain.objects.get_or_create(
            name='Postgraduate', opportunity_type=scholarship_type
        )

        # Software Specializations
        Specialization.objects.get_or_create(name='Backend', domain=software_domain)
        Specialization.objects.get_or_create(name='Frontend', domain=software_domain)
        Specialization.objects.get_or_create(name='Full Stack', domain=software_domain)
        Specialization.objects.get_or_create(name='DevOps', domain=software_domain)
        Specialization.objects.get_or_create(name='Mobile App', domain=software_domain)
        Specialization.objects.get_or_create(name='Machine Learning', domain=software_domain)

        # Data Science Specializations
        Specialization.objects.get_or_create(name='Data Analysis', domain=data_science_domain)
        Specialization.objects.get_or_create(name='Data Engineering', domain=data_science_domain)
        Specialization.objects.get_or_create(name='Business Intelligence', domain=data_science_domain)
        Specialization.objects.get_or_create(name='AI/ML Research', domain=data_science_domain)

        # Engineering Specializations
        Specialization.objects.get_or_create(name='Mechanical', domain=engineering_domain)
        Specialization.objects.get_or_create(name='Electrical', domain=engineering_domain)
        Specialization.objects.get_or_create(name='Civil', domain=engineering_domain)
        Specialization.objects.get_or_create(name='Chemical', domain=engineering_domain)

        # Healthcare Specializations
        Specialization.objects.get_or_create(name='Nursing', domain=healthcare_domain)
        Specialization.objects.get_or_create(name='Medical Research', domain=healthcare_domain)
        Specialization.objects.get_or_create(name='Healthcare Administration', domain=healthcare_domain)

        # Education Specializations
        Specialization.objects.get_or_create(name='Teaching', domain=education_domain)
        Specialization.objects.get_or_create(name='Educational Technology', domain=education_domain)
        Specialization.objects.get_or_create(name='Curriculum Development', domain=education_domain)

        # Marketing Specializations
        Specialization.objects.get_or_create(name='Digital Marketing', domain=marketing_domain)
        Specialization.objects.get_or_create(name='Content Marketing', domain=marketing_domain)
        Specialization.objects.get_or_create(name='Brand Management', domain=marketing_domain)

        # Design Specializations
        Specialization.objects.get_or_create(name='UI/UX Design', domain=design_domain)
        Specialization.objects.get_or_create(name='Graphic Design', domain=design_domain)
        Specialization.objects.get_or_create(name='Product Design', domain=design_domain)

        # Finance Specializations
        Specialization.objects.get_or_create(name='Accounting', domain=finance_domain)
        Specialization.objects.get_or_create(name='Financial Analysis', domain=finance_domain)
        Specialization.objects.get_or_create(name='Investment Banking', domain=finance_domain)

        # Masters Specializations
        Specialization.objects.get_or_create(name='Computer Science', domain=masters_domain)
        Specialization.objects.get_or_create(name='Business Administration', domain=masters_domain)
        Specialization.objects.get_or_create(name='Public Health', domain=masters_domain)
        Specialization.objects.get_or_create(name='Engineering', domain=masters_domain)
        Specialization.objects.get_or_create(name='Data Science', domain=masters_domain)

        # PhD Specializations
        Specialization.objects.get_or_create(name='Computer Science', domain=phd_domain)
        Specialization.objects.get_or_create(name='Engineering', domain=phd_domain)
        Specialization.objects.get_or_create(name='Public Health', domain=phd_domain)
        Specialization.objects.get_or_create(name='Business', domain=phd_domain)

        # Bachelors/PhD/Undergraduate/Postgraduate inherit similar specializations
        for domain in [bachelors_domain, undergraduate_domain, postgraduate_domain]:
            Specialization.objects.get_or_create(name='Computer Science', domain=domain)
            Specialization.objects.get_or_create(name='Engineering', domain=domain)
            Specialization.objects.get_or_create(name='Business', domain=domain)
            Specialization.objects.get_or_create(name='Healthcare', domain=domain)

        self.stdout.write(f'Created {OpportunityType.objects.count()} types, {Domain.objects.count()} domains, {Specialization.objects.count()} specializations')

    def _seed_locations(self):
        """Seed location hierarchy"""

        # Countries
        ethiopia, _ = Location.objects.get_or_create(name='Ethiopia')
        usa, _ = Location.objects.get_or_create(name='United States')
        uk, _ = Location.objects.get_or_create(name='United Kingdom')
        germany, _ = Location.objects.get_or_create(name='Germany')
        canada, _ = Location.objects.get_or_create(name='Canada')
        china, _ = Location.objects.get_or_create(name='China')
        japan, _ = Location.objects.get_or_create(name='Japan')
        australia, _ = Location.objects.get_or_create(name='Australia')
        france, _ = Location.objects.get_or_create(name='France')
        netherlands, _ = Location.objects.get_or_create(name='Netherlands')

        # Ethiopian Cities
        addis_ababa, _ = Location.objects.get_or_create(name='Addis Ababa', parent=ethiopia)
        Location.objects.get_or_create(name='Bole', parent=addis_ababa)
        Location.objects.get_or_create(name='Kazanchis', parent=addis_ababa)
        Location.objects.get_or_create(name='Piassa', parent=addis_ababa)

        # US Cities
        Location.objects.get_or_create(name='New York', parent=usa)
        Location.objects.get_or_create(name='San Francisco', parent=usa)
        Location.objects.get_or_create(name='Seattle', parent=usa)
        Location.objects.get_or_create(name='Austin', parent=usa)

        # UK Cities
        Location.objects.get_or_create(name='London', parent=uk)
        Location.objects.get_or_create(name='Manchester', parent=uk)
        Location.objects.get_or_create(name='Birmingham', parent=uk)

        # German Cities
        Location.objects.get_or_create(name='Berlin', parent=germany)
        Location.objects.get_or_create(name='Munich', parent=germany)
        Location.objects.get_or_create(name='Frankfurt', parent=germany)

        # Canadian Cities
        Location.objects.get_or_create(name='Toronto', parent=canada)
        Location.objects.get_or_create(name='Vancouver', parent=canada)
        Location.objects.get_or_create(name='Montreal', parent=canada)

        # Chinese Cities
        Location.objects.get_or_create(name='Beijing', parent=china)
        Location.objects.get_or_create(name='Shanghai', parent=china)
        Location.objects.get_or_create(name='Shenzhen', parent=china)

        # Japanese Cities
        Location.objects.get_or_create(name='Tokyo', parent=japan)
        Location.objects.get_or_create(name='Osaka', parent=japan)

        # Australian Cities
        Location.objects.get_or_create(name='Sydney', parent=australia)
        Location.objects.get_or_create(name='Melbourne', parent=australia)

        # European Cities
        Location.objects.get_or_create(name='Paris', parent=france)
        Location.objects.get_or_create(name='Amsterdam', parent=netherlands)

        # Remote location
        Location.objects.get_or_create(name='Remote')

        self.stdout.write(f'Created {Location.objects.count()} locations')

    def _seed_user_profiles(self):
        """Seed diverse user profiles for testing matching"""

        profiles_data = [
            {
                'email': 'backend.dev@example.com',
                'username': 'backend_dev',
                'full_name': 'Yonatan Backend',
                'telegram_id': 1001,
                'academic_info': {
                    'degree': 'BSc Computer Science',
                    'university': 'Addis Ababa Institute of Technology',
                    'graduation_year': 2022
                },
                'skills': ['Python', 'Django', 'PostgreSQL', 'REST APIs', 'Docker'],
                'interests': ['Backend Development', 'System Architecture', 'Open Source'],
                'languages': ['Amharic', 'English'],
            },
            {
                'email': 'frontend.dev@example.com',
                'username': 'frontend_dev',
                'full_name': 'Sarah Frontend',
                'telegram_id': 1002,
                'academic_info': {
                    'degree': 'BSc Software Engineering',
                    'university': 'Addis Ababa University',
                    'graduation_year': 2021
                },
                'skills': ['JavaScript', 'React', 'TypeScript', 'CSS', 'Node.js'],
                'interests': ['Frontend Development', 'UI/UX', 'Web Performance'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'data.scientist@example.com',
                'username': 'data_scientist',
                'full_name': 'Mary Data',
                'telegram_id': 1003,
                'academic_info': {
                    'degree': 'MSc Data Science',
                    'university': 'Addis Ababa University',
                    'graduation_year': 2023
                },
                'skills': ['Python', 'R', 'Machine Learning', 'TensorFlow', 'SQL', 'Tableau'],
                'interests': ['AI Research', 'Data Visualization', 'Predictive Analytics'],
                'languages': ['English'],
            },
            {
                'email': 'mobile.dev@example.com',
                'username': 'mobile_dev',
                'full_name': 'Alex Mobile',
                'telegram_id': 1004,
                'academic_info': {
                    'degree': 'BSc Computer Science',
                    'university': 'AAiT',
                    'graduation_year': 2022
                },
                'skills': ['Flutter', 'Dart', 'Firebase', 'Android', 'iOS', 'React Native'],
                'interests': ['Mobile Development', 'Cross-platform Apps', 'UX Design'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'finance.professional@example.com',
                'username': 'finance_pro',
                'full_name': 'David Finance',
                'telegram_id': 1005,
                'academic_info': {
                    'degree': 'MBA Finance',
                    'university': 'Addis Ababa University',
                    'graduation_year': 2020
                },
                'skills': ['Financial Analysis', 'Excel', 'Accounting', 'Budgeting', 'Financial Modeling'],
                'interests': ['Investment Banking', 'Financial Markets', 'Corporate Finance'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'healthcare.worker@example.com',
                'username': 'healthcare_worker',
                'full_name': 'Helen Healthcare',
                'telegram_id': 1006,
                'academic_info': {
                    'degree': 'BSc Nursing',
                    'university': 'Gondar University',
                    'graduation_year': 2021
                },
                'skills': ['Patient Care', 'Medical Research', 'Healthcare Administration', 'EMR Systems'],
                'interests': ['Public Health', 'Medical Research', 'Healthcare Innovation'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'graduate.student@example.com',
                'username': 'grad_student',
                'full_name': 'Emma Graduate',
                'telegram_id': 1007,
                'academic_info': {
                    'degree': 'BSc Computer Science',
                    'university': 'AAU',
                    'seeking': 'Masters in Data Science',
                    'graduation_year': 2023
                },
                'skills': ['Python', 'Java', 'Database Design', 'Statistics'],
                'interests': ['Graduate Studies', 'Research', 'Academic Career'],
                'languages': ['English'],
            },
            {
                'email': 'engineering.student@example.com',
                'username': 'engineering_student',
                'full_name': 'Michael Engineer',
                'telegram_id': 1008,
                'academic_info': {
                    'degree': 'BSc Mechanical Engineering',
                    'university': 'AAiT',
                    'graduation_year': 2024
                },
                'skills': ['CAD', 'SolidWorks', 'Thermodynamics', 'Fluid Mechanics', 'MATLAB'],
                'interests': ['Automotive Engineering', 'Renewable Energy', 'Product Design'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'design.professional@example.com',
                'username': 'design_pro',
                'full_name': 'Lisa Designer',
                'telegram_id': 1009,
                'academic_info': {
                    'degree': 'BFA Graphic Design',
                    'university': 'Entoto TVET',
                    'graduation_year': 2022
                },
                'skills': ['Adobe Creative Suite', 'UI/UX Design', 'Branding', 'Illustration', 'Figma'],
                'interests': ['Digital Art', 'Brand Strategy', 'Design Systems'],
                'languages': ['English', 'Amharic'],
            },
            {
                'email': 'business.student@example.com',
                'username': 'business_student',
                'full_name': 'Carlos Business',
                'telegram_id': 1010,
                'academic_info': {
                    'degree': 'BBA Management',
                    'university': 'Addis Ababa University',
                    'graduation_year': 2024
                },
                'skills': ['Business Analysis', 'Project Management', 'Marketing', 'Excel', 'PowerPoint'],
                'interests': ['Entrepreneurship', 'International Business', 'Startups'],
                'languages': ['English', 'Spanish', 'Amharic'],
            },
        ]

        created_profiles = []
        for profile_data in profiles_data:
            # Get or create user
            user, user_created = User.objects.get_or_create(
                email=profile_data['email']
            )

            # Set password if user was created
            if user_created:
                user.set_password('password123')
                user.save()

            # Get or create profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': profile_data['full_name'],
                    'telegram_id': profile_data['telegram_id'],
                    'academic_info': profile_data['academic_info'],
                    'skills': profile_data['skills'],
                    'interests': profile_data['interests'],
                    'languages': profile_data['languages'],
                }
            )

            # Always update profile data (in case it was created empty)
            profile.full_name = profile_data['full_name']
            profile.telegram_id = profile_data['telegram_id']
            profile.academic_info = profile_data['academic_info']
            profile.skills = profile_data['skills']
            profile.interests = profile_data['interests']
            profile.languages = profile_data['languages']
            profile.save()

            if profile_created:
                self.stdout.write(f'Created profile for: {profile.full_name}')
            else:
                self.stdout.write(f'Updated profile for: {profile.full_name}')

            created_profiles.append(profile)

        self.stdout.write(f'Processed {len(created_profiles)} user profiles')
