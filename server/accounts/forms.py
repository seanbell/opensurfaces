from django import forms
from captcha.fields import CaptchaField
import account.forms


class SignupForm(account.forms.SignupForm):

    captcha = CaptchaField()

    def clean_username(self):
        username = self.cleaned_data['username']
        if username.startswith('mturk_'):
            raise forms.ValidationError("Usernames that start with 'mturk_'are reserved.  Please choose another.")
        if username.startswith('mt_'):
            raise forms.ValidationError("Usernames that start with 'mt_'are reserved.  Please choose another.")
        return super(SignupForm, self).clean_username()


class LoginUsernameOrEmailForm(account.forms.LoginForm):

    username = forms.CharField(label="Username or Email")
    authentication_fail_message = "The username and/or password you specified are not correct."
    identifier_field = "username"

    def __init__(self, *args, **kwargs):
        super(LoginUsernameOrEmailForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ["username", "password", "remember"]
