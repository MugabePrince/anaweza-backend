# Utility script to verify migration
# Create this as: job_seeker/management/commands/verify_skills_migration.py

from django.core.management.base import BaseCommand
from job_seeker.models import JobSeeker
import json

class Command(BaseCommand):
    help = 'Verify skills migration by checking data integrity'
    
    def handle(self, *args, **options):
        job_seekers = JobSeeker.objects.all()
        
        json_format_count = 0
        old_format_count = 0
        empty_skills_count = 0
        invalid_json_count = 0
        
        for job_seeker in job_seekers:
            if not job_seeker.skills:
                empty_skills_count += 1
            elif job_seeker.skills.strip().startswith('['):
                try:
                    skills_data = json.loads(job_seeker.skills)
                    if isinstance(skills_data, list):
                        json_format_count += 1
                        
                        # Verify each skill has required fields
                        for skill in skills_data:
                            if not isinstance(skill, dict) or 'name' not in skill or 'experience' not in skill:
                                self.stderr.write(
                                    f"Invalid skill format in Job Seeker {job_seeker.id}: {skill}"
                                )
                    else:
                        invalid_json_count += 1
                        self.stderr.write(
                            f"Invalid JSON structure in Job Seeker {job_seeker.id}: {job_seeker.skills[:100]}..."
                        )
                except json.JSONDecodeError:
                    invalid_json_count += 1
                    self.stderr.write(
                        f"Invalid JSON in Job Seeker {job_seeker.id}: {job_seeker.skills[:100]}..."
                    )
            else:
                old_format_count += 1
        
        # Print summary
        total = job_seekers.count()
        self.stdout.write(f"\nSKILLS MIGRATION VERIFICATION REPORT")
        self.stdout.write(f"=" * 40)
        self.stdout.write(f"Total Job Seekers: {total}")
        self.stdout.write(f"JSON format (migrated): {json_format_count}")
        self.stdout.write(f"Old format (not migrated): {old_format_count}")
        self.stdout.write(f"Empty skills: {empty_skills_count}")
        self.stdout.write(f"Invalid JSON: {invalid_json_count}")
        
        if old_format_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n{old_format_count} job seekers still need migration")
            )
        
        if invalid_json_count > 0:
            self.stdout.write(
                self.style.ERROR(f"\n{invalid_json_count} job seekers have invalid JSON data")
            )
        
        if json_format_count == total - empty_skills_count:
            self.stdout.write(
                self.style.SUCCESS("\n✓ All job seekers with skills have been successfully migrated!")
            )