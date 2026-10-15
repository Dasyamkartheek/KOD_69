from django import forms
from django.conf import settings
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from secrets import compare_digest
from .models import (
    Program, ProgramRegistration, ProgrammingChallenge, ProgrammingTestCase,
    StudentProfile,
)

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    registration_number = forms.CharField(max_length=40, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            StudentProfile.objects.update_or_create(
                user=user,
                defaults={'registration_number': self.cleaned_data['registration_number'], 'role': 'student'}
            )
        return user

class AdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        has_admin_role = StudentProfile.objects.filter(user=user, role='admin').exists()
        if not (user.is_staff or user.is_superuser or has_admin_role):
            raise forms.ValidationError(
                'This account does not have admin access.', code='not_admin',
            )

class AdminSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    invite_code = forms.CharField(
        label='Admin invitation code',
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, allow_bootstrap=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_bootstrap = allow_bootstrap
        if allow_bootstrap:
            self.fields['invite_code'].required = False
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_invite_code(self):
        invite_code = self.cleaned_data['invite_code']
        configured_code = settings.ADMIN_SIGNUP_CODE
        if self.allow_bootstrap and not configured_code and not invite_code:
            return invite_code
        if not configured_code or not compare_digest(invite_code, configured_code):
            raise forms.ValidationError('The admin invitation code is invalid or signup is disabled.')
        return invite_code

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            StudentProfile.objects.update_or_create(user=user, defaults={'role': 'admin'})
        return user

class ProgrammingChallengeForm(forms.ModelForm):
    class Meta:
        model = ProgrammingChallenge
        fields = (
            'title', 'description', 'topic', 'difficulty', 'sample_input',
            'sample_output', 'marks', 'published',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'sample_input': forms.Textarea(attrs={'rows': 3}),
            'sample_output': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css_class

class ProgrammingTestCaseForm(forms.ModelForm):
    class Meta:
        model = ProgrammingTestCase
        fields = ('name', 'input_data', 'expected_output', 'order')
        widgets = {
            'input_data': forms.Textarea(attrs={'rows': 3}),
            'expected_output': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css_class

class BaseProgrammingTestCaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        active_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
            and (form.instance.pk or form.has_changed())
        ]
        if not active_forms:
            raise forms.ValidationError('Add at least one test case.')

ProgrammingTestCaseFormSet = inlineformset_factory(
    ProgrammingChallenge,
    ProgrammingTestCase,
    form=ProgrammingTestCaseForm,
    formset=BaseProgrammingTestCaseFormSet,
    fields=('name', 'input_data', 'expected_output', 'order'),
    extra=1,
    can_delete=True,
)

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = (
            'title', 'organization', 'program_type', 'description', 'eligibility',
            'registration_deadline', 'start_date', 'end_date', 'delivery_mode',
            'location', 'published',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'eligibility': forms.Textarea(attrs={'rows': 3}),
            'registration_deadline': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css_class

    def clean(self):
        cleaned_data = super().clean()
        registration_deadline = cleaned_data.get('registration_deadline')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if registration_deadline and start_date and registration_deadline > start_date:
            self.add_error('registration_deadline', 'Registration must close on or before the program starts.')
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'The end date must be on or after the start date.')
        return cleaned_data

class ProgramResultForm(forms.ModelForm):
    class Meta:
        model = ProgramRegistration
        fields = ('result_status', 'score', 'feedback', 'result_published')
        widgets = {'feedback': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['score'].widget.attrs.update({'min': '0', 'step': '0.01'})
        for field in self.fields.values():
            css_class = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css_class

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and score < 0:
            raise forms.ValidationError('Score cannot be negative.')
        return score
