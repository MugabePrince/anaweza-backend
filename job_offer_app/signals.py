from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import JobOffer
from job_seeker.models import JobSeeker

@receiver(post_save, sender=JobOffer)
def notify_matching_job_seekers(sender, instance, created, **kwargs):
    if created:  # Only trigger for newly created JobOffer
        job_requirements = set(instance.requirements)  # Convert requirements to a set for easier comparison
        
        # Find job seekers whose skills match the job requirements
        matching_job_seekers = JobSeeker.objects.filter(
            user__status=True,  # Only active users
            skills__isnull=False,  # Ensure skills are not empty
        )
        
        for job_seeker in matching_job_seekers:
            seeker_skills = {skill.strip().lower() for skill in job_seeker.skills.split(',')}
            
            # Check if any skill matches the job requirements
            if seeker_skills.intersection({req.lower() for req in job_requirements}):
                send_job_notification_email(job_seeker, instance)

def send_job_notification_email(job_seeker, job_offer):
    subject = f"New Job Opportunity Matching Your Skills: {job_offer.title}"
    
    # Render HTML email template (optional)
    message = render_to_string('job_notification_email.html', {
        'job_seeker': job_seeker,
        'job_offer': job_offer,
        'site_url': 'https://www.anaweza.com',
    })
    
    # Plain text fallback
    plain_message = f"""
    Hello {job_seeker.first_name},
    
    A new job opportunity matching your skills has been posted on Anaweza:
    
    Job Title: {job_offer.title}
    Company: {job_offer.company_name or 'N/A'}
    Location: {job_offer.location}
    Deadline: {job_offer.deadline}
    
    Visit https://www.anaweza.com to apply!
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [job_seeker.user.email],  # Send to job seeker's email
        html_message=message,
        fail_silently=False,
    )