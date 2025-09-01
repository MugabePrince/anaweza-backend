# Django Migration
# Create this as: job_seeker/migrations/XXXX_enhance_skills_field.py

from django.db import migrations, models
import json

def migrate_skills_to_json(apps, schema_editor):
    """
    Convert existing skills from comma-separated string to JSON format with default experience
    """
    JobSeeker = apps.get_model('job_seeker', 'JobSeeker')
    
    for job_seeker in JobSeeker.objects.all():
        if job_seeker.skills and not job_seeker.skills.startswith('['):
            # Parse old comma-separated skills
            old_skills = [skill.strip() for skill in job_seeker.skills.split(',') if skill.strip()]
            
            # Convert to new format with default experience
            skills_with_experience = []
            for skill in old_skills:
                # Check if skill already has experience info (like "Python (3-5 years)")
                if '(' in skill and 'years' in skill:
                    # Extract skill name and experience
                    parts = skill.split('(')
                    skill_name = parts[0].strip()
                    experience_part = parts[1].replace(')', '').replace('years', '').strip()
                    
                    skills_with_experience.append({
                        'name': skill_name,
                        'experience': experience_part
                    })
                else:
                    # Default experience for skills without specified experience
                    skills_with_experience.append({
                        'name': skill,
                        'experience': '1-3'  # Default to junior level
                    })
            
            # Save as JSON
            job_seeker.skills = json.dumps(skills_with_experience)
            job_seeker.save()

def reverse_migrate_skills_from_json(apps, schema_editor):
    """
    Reverse migration: Convert JSON skills back to comma-separated string
    """
    JobSeeker = apps.get_model('job_seeker', 'JobSeeker')
    
    for job_seeker in JobSeeker.objects.all():
        if job_seeker.skills and job_seeker.skills.startswith('['):
            try:
                skills_data = json.loads(job_seeker.skills)
                skill_names = [skill['name'] for skill in skills_data if 'name' in skill]
                job_seeker.skills = ', '.join(skill_names)
                job_seeker.save()
            except json.JSONDecodeError:
                # Skip if JSON is invalid
                continue

class Migration(migrations.Migration):
    
    dependencies = [
        ('job_seeker', '0001_initial'),  # Replace with your last migration
    ]
    
    operations = [
        # Add the new skills_old field for backward compatibility
        migrations.AddField(
            model_name='jobseeker',
            name='skills_old',
            field=models.TextField(blank=True, help_text='Deprecated: Comma-separated skills'),
        ),
        
        # Run data migration to convert existing skills
        migrations.RunPython(
            migrate_skills_to_json,
            reverse_migrate_skills_from_json,
        ),
        
        # Update the help text for the skills field
        migrations.AlterField(
            model_name='jobseeker',
            name='skills',
            field=models.TextField(blank=True, help_text='JSON string containing skills with experience levels'),
        ),
    ]
