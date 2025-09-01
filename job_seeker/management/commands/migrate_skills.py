# Management command to migrate skills data
# Create this as: job_seeker/management/commands/migrate_skills.py

from django.core.management.base import BaseCommand
from django.db import transaction
from job_seeker.models import JobSeeker
import json
import re

class Command(BaseCommand):
    help = 'Migrate existing skills data to new JSON format with experience levels'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--default-experience',
            type=str,
            default='1-3',
            help='Default experience level for skills without specified experience',
        )
    
    def parse_skill_with_experience(self, skill_text):
        """
        Parse skill text that might contain experience info
        Examples:
        - "Python (3-5 years)" -> {'name': 'Python', 'experience': '3-5'}
        - "JavaScript" -> {'name': 'JavaScript', 'experience': default}
        """
        # Pattern to match: "Skill Name (X-Y years)" or "Skill Name (X+ years)"
        match = re.match(r'^(.+?)\s*\(([^)]+)\s*years?\)$', skill_text.strip())
        
        if match:
            skill_name = match.group(1).strip()
            experience_part = match.group(2).strip()
            # Clean up experience (remove 'years' if present)
            experience = re.sub(r'\s*years?$', '', experience_part)
            return {
                'name': skill_name,
                'experience': experience
            }
        else:
            return {
                'name': skill_text.strip(),
                'experience': self.default_experience
            }
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.default_experience = options['default_experience']
        
        job_seekers = JobSeeker.objects.all()
        migrated_count = 0
        error_count = 0
        
        self.stdout.write(f"Found {job_seekers.count()} job seekers to process...")
        
        for job_seeker in job_seekers:
            try:
                # Skip if already in JSON format
                if job_seeker.skills and job_seeker.skills.strip().startswith('['):
                    continue
                
                # Parse old format skills
                if job_seeker.skills:
                    # Store old skills in skills_old field for backup
                    old_skills_backup = job_seeker.skills
                    
                    # Parse comma-separated skills
                    skill_items = [item.strip() for item in job_seeker.skills.split(',') if item.strip()]
                    
                    # Convert each skill
                    skills_with_experience = []
                    for skill_item in skill_items:
                        skill_data = self.parse_skill_with_experience(skill_item)
                        skills_with_experience.append(skill_data)
                    
                    if self.dry_run:
                        self.stdout.write(
                            f"DRY RUN - Job Seeker {job_seeker.id} ({job_seeker.first_name} {job_seeker.last_name}):"
                        )
                        self.stdout.write(f"  Old: {old_skills_backup}")
                        self.stdout.write(f"  New: {json.dumps(skills_with_experience, indent=2)}")
                        self.stdout.write("")
                    else:
                        # Save backup and new format
                        job_seeker.skills_old = old_skills_backup
                        job_seeker.skills = json.dumps(skills_with_experience)
                        job_seeker.save()
                        
                        self.stdout.write(
                            f"✓ Migrated Job Seeker {job_seeker.id} ({job_seeker.first_name} {job_seeker.last_name})"
                        )
                    
                    migrated_count += 1
                
            except Exception as e:
                error_count += 1
                self.stderr.write(
                    f"✗ Error processing Job Seeker {job_seeker.id}: {str(e)}"
                )
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(f"\nDRY RUN COMPLETE:")
            )
            self.stdout.write(f"Would migrate {migrated_count} job seekers")
            self.stdout.write(f"Errors encountered: {error_count}")
            self.stdout.write("\nRun without --dry-run to apply changes")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nMIGRATION COMPLETE:")
            )
            self.stdout.write(f"Successfully migrated {migrated_count} job seekers")
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f"Errors encountered: {error_count}")
                )
