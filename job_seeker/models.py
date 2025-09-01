from django.db import models
from django.conf import settings
from django.utils.timezone import now
from userApp.models import CustomUser
import json
import re

class JobSeeker(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    EDUCATION_CHOICES = [
        ('none', 'No Formal Education'),
        ('primary', 'Primary Education'),
        ('ordinary_level', 'Ordinary Level'),
        ('advanced_diploma', 'Advanced Diploma'),
        ('secondary', 'Secondary Education'),
        ('vocational', 'Vocational Training'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='job_seeker')
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Enhanced skills field to store JSON data
    skills = models.TextField(blank=True, help_text="JSON string containing skills with experience levels")
    
    # Keep the old skills field for backward compatibility (deprecated)
    skills_old = models.TextField(blank=True, null=True, help_text="Deprecated: Comma-separated skills")

    experience = models.IntegerField(default=0, help_text="Overall years of experience (auto-calculated)")
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES, default='none')
    education_sector = models.CharField(max_length=100, blank=True, null=True, help_text="Field of study (if applicable)")
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    salary_range = models.CharField(max_length=50, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    renewal_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_job_seekers')
    created_at = models.DateTimeField(default=now)
    status = models.BooleanField(default=False)
    district = models.CharField(max_length=30, default='', blank=True, null=True)
    sector = models.CharField(max_length=30, default='', blank=True, null=True)
    
    def _parse_experience_range(self, experience_str):
        """
        Parse experience range string and return the maximum value
        Examples: '1-3' -> 3, '5+' -> 5, '8+' -> 8, '0-1' -> 1
        """
        if not experience_str:
            return 0
            
        experience_str = str(experience_str).strip()
        
        # Handle ranges like '1-3', '3-5', etc.
        range_match = re.match(r'(\d+)-(\d+)', experience_str)
        if range_match:
            return int(range_match.group(2))  # Return the upper bound
        
        # Handle formats like '5+', '8+', etc.
        plus_match = re.match(r'(\d+)\+', experience_str)
        if plus_match:
            return int(plus_match.group(1))
        
        # Handle single numbers
        number_match = re.match(r'(\d+)', experience_str)
        if number_match:
            return int(number_match.group(1))
        
        return 0
    
    def calculate_overall_experience(self):
        """
        Calculate overall experience based on individual skill experience levels
        Takes the maximum experience from all skills
        """
        skills_data = self.get_skills_with_experience()
        if not skills_data:
            return 0
        
        max_experience = 0
        for skill in skills_data:
            if 'experience' in skill:
                skill_exp = self._parse_experience_range(skill['experience'])
                max_experience = max(max_experience, skill_exp)
        
        return max_experience
    
    def set_skills_with_experience(self, skills_list):
        """
        Set skills with their experience levels and auto-calculate overall experience
        Expected format: [{'name': 'Python', 'experience': '3-5'}, ...]
        """
        if isinstance(skills_list, list):
            self.skills = json.dumps(skills_list)
        else:
            self.skills = json.dumps([])
        
        # Auto-calculate overall experience
        self.experience = self.calculate_overall_experience()
    
    def get_skills_with_experience(self):
        """
        Get skills with their experience levels as a list of dictionaries
        Returns: [{'name': 'Python', 'experience': '3-5'}, ...]
        """
        try:
            if self.skills:
                return json.loads(self.skills)
            return []
        except json.JSONDecodeError:
            return []
    
    def get_skills_list(self):
        """
        Get just the skill names as a list
        Returns: ['Python', 'JavaScript', ...]
        """
        skills_data = self.get_skills_with_experience()
        return [skill['name'] for skill in skills_data if 'name' in skill]
    
    def get_skills_display(self):
        """
        Get skills formatted for display
        Returns: "Python (3-5 years), JavaScript (1-3 years)"
        """
        skills_data = self.get_skills_with_experience()
        formatted_skills = []
        for skill in skills_data:
            if 'name' in skill and 'experience' in skill:
                formatted_skills.append(f"{skill['name']} ({skill['experience']} years)")
        return ", ".join(formatted_skills)
    
    def save(self, *args, **kwargs):
        """
        Override save method to auto-calculate experience before saving
        """
        # Auto-calculate overall experience if skills are set
        if self.skills:
            self.experience = self.calculate_overall_experience()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone_number})"


# Alternative approach: Separate Skill model for more normalized data
class JobSeekerSkill(models.Model):
    """
    Alternative normalized approach - separate table for skills
    Use this if you prefer normalized database design
    """
    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='job_seeker_skills')
    skill_name = models.CharField(max_length=100)
    experience_level = models.CharField(max_length=20, help_text="e.g., '0-1', '1-3', '3-5', '5-8', '8+'")
    created_at = models.DateTimeField(default=now)
    
    class Meta:
        unique_together = ['job_seeker', 'skill_name']
    
    def save(self, *args, **kwargs):
        """
        Override save method to update JobSeeker's overall experience
        """
        super().save(*args, **kwargs)
        # Recalculate JobSeeker's overall experience
        self.job_seeker.experience = self.job_seeker.calculate_overall_experience_from_skills()
        self.job_seeker.save()
    
    def delete(self, *args, **kwargs):
        """
        Override delete method to update JobSeeker's overall experience
        """
        job_seeker = self.job_seeker
        super().delete(*args, **kwargs)
        # Recalculate JobSeeker's overall experience after deletion
        job_seeker.experience = job_seeker.calculate_overall_experience_from_skills()
        job_seeker.save()
    
    def __str__(self):
        return f"{self.job_seeker.first_name} {self.job_seeker.last_name} - {self.skill_name} ({self.experience_level} years)"


# Extension to JobSeeker model for normalized skills approach
def calculate_overall_experience_from_skills(self):
    """
    Calculate overall experience from JobSeekerSkill records
    This method works with the normalized JobSeekerSkill model
    """
    skills = self.job_seeker_skills.all()
    if not skills.exists():
        return 0
    
    max_experience = 0
    for skill in skills:
        skill_exp = self._parse_experience_range(skill.experience_level)
        max_experience = max(max_experience, skill_exp)
    
    return max_experience

# Add the method to JobSeeker model
JobSeeker.calculate_overall_experience_from_skills = calculate_overall_experience_from_skills