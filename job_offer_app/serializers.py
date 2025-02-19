from rest_framework import serializers
from .models import JobOffer
from userApp.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'status', 'created_at']

class JobOfferSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = JobOffer
        fields = '__all__'
        read_only_fields = ['created_by']

    def create(self, validated_data):
        user = self.context['request'].user
        job_offer = JobOffer.objects.create(created_by=user, **validated_data)
        return job_offer