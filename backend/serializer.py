
from rest_framework import serializers
from .models import User, Skill, HackathonExperience


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class HackathonExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HackathonExperience
        fields = ["id", "organizer_name", "hackathon_name", "description", "achievements", "created_at"]
        extra_kwargs = {
            'created_at': {'read_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    # CORRECTED: Make username/password optional for updates
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    # For backward compatibility with existing fields
    skills = serializers.CharField(write_only=True, required=False)
    my_skills = SkillSerializer(many=True, read_only=True)

    # Frontend compatibility fields
    knownSkills = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    desiredSkills = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    known_skills = SkillSerializer(many=True, read_only=True)
    desired_skills = SkillSerializer(many=True, read_only=True)

    # Social links mapping
    linkedin = serializers.URLField(write_only=True, required=False, allow_blank=True)
    github = serializers.URLField(write_only=True, required=False, allow_blank=True)
    linkedin_url = serializers.URLField(read_only=True)
    github_url = serializers.URLField(read_only=True)

    # CORRECTED: College field mapping
    college = serializers.CharField(write_only=True, required=False, allow_blank=True)
    college_name = serializers.CharField(read_only=True)

    # Beginner field
    isBeginner = serializers.BooleanField(write_only=True, required=False)
    is_beginner = serializers.BooleanField(read_only=True)

    # Hackathon experiences
    hackathonExperiences = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    hackathon_experiences = HackathonExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "password", "name", "college_name", "year", "email",
            "gender", "skills", "my_skills",
            "linkedin_url", "github_url", "is_beginner",
            "known_skills", "desired_skills", "created_at", "updated_at",
            "knownSkills", "desiredSkills", "linkedin", "github", "college", "isBeginner",
            "hackathonExperiences", "hackathon_experiences"
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # If this is an update operation make fields optional
        if self.instance:
            print(" SERIALIZER DEBUG - Update mode: making username/password optional")
            self.fields['username'].required = False
            self.fields['password'].required = False
        else:
            print(" SERIALIZER DEBUG - Create mode: username/password required")
            self.fields['username'].required = True
            self.fields['password'].required = True

    def validate_username(self, value):
        # Only validate uniqueness if username is being changed
        if self.instance and self.instance.username == value:
            return value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        # Only validate uniqueness if email is being changed
        if self.instance and self.instance.email == value:
            return value
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        print(" SERIALIZER DEBUG - Creating user with data:", validated_data)

        # Username and password are required for creation
        if not validated_data.get('username'):
            raise serializers.ValidationError({"username": "Username is required for user creation."})
        if not validated_data.get('password'):
            raise serializers.ValidationError({"password": "Password is required for user creation."})

        # Extract password
        password = validated_data.pop('password')

        # Handle different skill input formats
        skills_text = validated_data.pop("skills", "")
        known_skills_list = validated_data.pop("knownSkills", [])
        desired_skills_list = validated_data.pop("desiredSkills", [])

        # Handle hackathon experiences with detailed logging
        hackathon_experiences_list = validated_data.pop("hackathonExperiences", [])
        print(f" SERIALIZER DEBUG - Hackathon experiences received: {hackathon_experiences_list}")

        # Handle college field mapping
        college = validated_data.pop("college", None)
        if college:
            validated_data["college_name"] = college.strip()
            print(f" SERIALIZER DEBUG - College mapped: {college} -> {validated_data['college_name']}")

        # Handle social links
        linkedin = validated_data.pop("linkedin", None)
        github = validated_data.pop("github", None)
        is_beginner = validated_data.pop("isBeginner", False)

        if linkedin:
            validated_data["linkedin_url"] = linkedin
        if github:
            validated_data["github_url"] = github
        validated_data["is_beginner"] = is_beginner

        print(f" SERIALIZER DEBUG - Final validated_data before user creation: {validated_data}")

        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        print(f" SERIALIZER DEBUG - User created with ID: {user.id}")

        # Handle backward compatibility skills
        if skills_text:
            skills_list = [s.strip().lower() for s in skills_text.split(",") if s.strip()]
            for skill_name in skills_list:
                skill, _ = Skill.objects.get_or_create(name=skill_name.capitalize())
                user.my_skills.add(skill)

        # Handle known skills
        for skill_name in known_skills_list:
            if skill_name.strip():
                skill, _ = Skill.objects.get_or_create(name=skill_name.strip().capitalize())
                user.known_skills.add(skill)
                user.my_skills.add(skill)  # Also add to my_skills for backward compatibility

        # Handle desired skills
        for skill_name in desired_skills_list:
            if skill_name.strip():
                skill, _ = Skill.objects.get_or_create(name=skill_name.strip().capitalize())
                user.desired_skills.add(skill)

        # CORRECTED: Handle hackathon experiences
        experiences_created = 0
        for exp_data in hackathon_experiences_list:
            print(f" SERIALIZER DEBUG - Processing experience: {exp_data}")

            organizer = exp_data.get('organizer_name', '').strip()
            hackathon = exp_data.get('hackathon_name', '').strip()

            if organizer and hackathon:
                experience = HackathonExperience.objects.create(
                    user=user,
                    organizer_name=organizer,
                    hackathon_name=hackathon,
                    description=exp_data.get('description', '').strip(),
                    achievements=exp_data.get('achievements', '').strip()
                )
                experiences_created += 1
                print(f" SERIALIZER DEBUG - Created experience ID: {experience.id}")
            else:
                print(
                    f" SERIALIZER DEBUG - Skipped experience due to missing required fields: organizer='{organizer}', hackathon='{hackathon}'")

        print(f" SERIALIZER DEBUG - Created {experiences_created} hackathon experiences for user {user.id}")

        return user

    def update(self, instance, validated_data):
        print(f" SERIALIZER DEBUG - Updating user {instance.id} with data: {validated_data}")

        #Don't require username/password for updates
        validated_data.pop('username', None)  # Remove username from updates
        password = validated_data.pop('password', None)  # Only update password if provided

        # Handle hackathon experiences update
        hackathon_experiences_list = validated_data.pop("hackathonExperiences", None)

        # Handle college field mapping for updates
        college = validated_data.pop("college", None)
        if college is not None:
            print(f" SERIALIZER DEBUG - Setting college_name to: '{college}'")
            instance.college_name = college.strip() if college and college.strip() else None

        # Handle skills
        known_skills_list = validated_data.pop("knownSkills", None)
        desired_skills_list = validated_data.pop("desiredSkills", None)

        # Update basic fields only if provided
        for field in ['name', 'email', 'year', 'gender']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                print(f"SERIALIZER DEBUG - Updated {field}: {validated_data[field]}")

        # Handle social links
        linkedin = validated_data.pop("linkedin", None)
        github = validated_data.pop("github", None)
        is_beginner = validated_data.pop("isBeginner", None)

        if linkedin is not None:
            instance.linkedin_url = linkedin
        if github is not None:
            instance.github_url = github
        if is_beginner is not None:
            instance.is_beginner = is_beginner

        #Only update password if provided
        if password:
            instance.set_password(password)
            print(" SERIALIZER DEBUG - Password updated")

        instance.save()
        print(f" SERIALIZER DEBUG - User {instance.id} saved with college_name: '{instance.college_name}'")

        # Update skills if provided
        if known_skills_list is not None:
            instance.known_skills.clear()
            instance.my_skills.clear()
            for skill_name in known_skills_list:
                if skill_name.strip():
                    skill, _ = Skill.objects.get_or_create(name=skill_name.strip().capitalize())
                    instance.known_skills.add(skill)
                    instance.my_skills.add(skill)

        if desired_skills_list is not None:
            instance.desired_skills.clear()
            for skill_name in desired_skills_list:
                if skill_name.strip():
                    skill, _ = Skill.objects.get_or_create(name=skill_name.strip().capitalize())
                    instance.desired_skills.add(skill)

        # Update hackathon experiences
        if hackathon_experiences_list is not None:
            print(f" SERIALIZER DEBUG - Updating hackathon experiences: {hackathon_experiences_list}")

            # Clear existing experiences
            instance.hackathon_experiences.all().delete()

            # Add new experiences
            experiences_created = 0
            for exp_data in hackathon_experiences_list:
                organizer = exp_data.get('organizer_name', '').strip()
                hackathon = exp_data.get('hackathon_name', '').strip()

                if organizer and hackathon:
                    experience = HackathonExperience.objects.create(
                        user=instance,
                        organizer_name=organizer,
                        hackathon_name=hackathon,
                        description=exp_data.get('description', '').strip(),
                        achievements=exp_data.get('achievements', '').strip()
                    )
                    experiences_created += 1
                    print(f" SERIALIZER DEBUG - Updated experience ID: {experience.id}")

            print(f" SERIALIZER DEBUG - Updated {experiences_created} hackathon experiences for user {instance.id}")

        return instance
