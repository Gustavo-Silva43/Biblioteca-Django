from django.contrib import messages
from django import forms
from django.shortcuts import redirect
from .models import Usuario
from django.contrib.auth.hashers import make_password  

class UsuarioCadastroForm(forms.ModelForm):
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['reader_ref_id', 'reader_name', 'reader_contact',
                  'reader_address', 'email', 'login', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password) 
        user.tipo_usuario = 'Membro_comum'
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save() 
        return user


class UsuarioRegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirme a Senha")
    
    secret_key = forms.CharField(max_length=100, required=False, label="Palavra Chave de Registro (Opcional)")

    class Meta:
        model = Usuario
        fields = ['reader_name', 'email', 'login', 'password', 'password_confirm', 
                  'reader_contact', 'reader_address', 'tipo_usuario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_usuario'].initial = 'membro_comum' 

        self.fields['secret_key'].widget.attrs.update({
            'placeholder': 'Deixe em branco para Membro Comum',
            'class': 'form-control'
        })


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        login = cleaned_data.get('login')
        email = cleaned_data.get('email')
        tipo_usuario = cleaned_data.get('tipo_usuario')
        secret_key = cleaned_data.get('secret_key')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', 'As senhas não coincidem.')
        elif not password:
            self.add_error('password', 'Por favor, crie uma senha.')
        elif not password_confirm:
            self.add_error('password_confirm', 'Confirme a senha.')

        if Usuario.objects.filter(login=login).exists():
            self.add_error('login', 'Este nome de usuário já está em uso. Por favor, escolha outro.')

        if email and Usuario.objects.filter(email=email).exists():
            self.add_error('email', 'Este e-mail já está cadastrado. Tente fazer login ou use outro e-mail.')

        if tipo_usuario == 'membro_comum' and secret_key:
            self.add_error('secret_key', 'Palavra Chave não é necessária para Membro Comum.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password) 

        if user.tipo_usuario == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif user.tipo_usuario == 'funcionario':
            user.is_staff = True
            user.is_superuser = False 
        else: 
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
        return user


class UsuarioAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Deixe em branco para manter a senha atual.")
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Confirme a nova senha.")
    
    class Meta:
        model = Usuario
        fields = ['reader_name', 'reader_contact', 'reader_address', 'email', 'login', 'password', 'password_confirm', 'tipo_usuario']

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None) 
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['password'].widget.attrs['value'] = ''
            self.fields['password'].required = False 
            self.fields['password_confirm'].required = False 

        if self.request_user and self.request_user.tipo_usuario.lower() == 'funcionario':
            self.fields['tipo_usuario'].choices = [('membro_comum', 'Membro Comum')]
            if self.instance and self.instance.pk and self.instance.tipo_usuario.lower() != 'membro_comum':
                del self.fields['tipo_usuario'] 

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password or password_confirm:
            if password and password_confirm:
                if password != password_confirm:
                    self.add_error('password_confirm', 'As senhas não coincidem.')
            elif password and not password_confirm:
                self.add_error('password_confirm', 'Confirme a senha.')
            elif not password and password_confirm:
                self.add_error('password', 'Digite a senha.')
        
        if self.request_user and self.request_user.tipo_usuario.lower() == 'funcionario':
            if 'tipo_usuario' in cleaned_data and cleaned_data['tipo_usuario'].lower() != 'membro_comum':
                self.add_error('tipo_usuario', 'Funcionários só podem cadastrar ou alterar para "Membro Comum".')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        if password: 
            user.set_password(password)
        
        if self.request_user and self.request_user.tipo_usuario.lower() == 'funcionario':
            if 'tipo_usuario' in self.cleaned_data: 
                 user.tipo_usuario = 'membro_comum'

        if commit:
            user.save()
        return user
    
class UsuarioLoginForm(forms.Form):
    login = forms.CharField(max_length=150, label="Nome de Usuário para Login")
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")