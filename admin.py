from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import Livro, Emprestimo, Usuario

admin.site.register(Usuario)
admin.site.register(Livro)
admin.site.register(Emprestimo) 