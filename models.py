from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone 
from datetime import timedelta


class UsuarioManager(BaseUserManager):
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('O campo de login é obrigatório')
        email = extra_fields.get('email')
        if email:
            email = self.normalize_email(email)
            extra_fields['email'] = email
        user = self.model(login=login, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('tipo_usuario', 'admin') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('tipo_usuario') != 'admin':
            raise ValueError('Superuser must have tipo_usuario="admin".')
        
        return self.create_user(login, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'), 
        ('funcionario', 'Funcionário'), 
        ('membro_comum', 'Membro Comum'), 
    ]

    reader_ref_id = models.CharField(max_length=100, unique=True, null=True, blank=True, 
                                     verbose_name='ID de Referência do Leitor')
    reader_name = models.CharField(max_length=200, verbose_name='Nome Completo')
    reader_contact = models.CharField(max_length=50, blank=True, null=True, 
                                      verbose_name='Contato')
    reader_address = models.TextField(blank=True, null=True, verbose_name='Endereço')
    email = models.EmailField(max_length=254, unique=True, blank=True, null=True, 
                              verbose_name='E-mail')

    login = models.CharField(max_length=100, unique=True, verbose_name='Nome de Usuário para Login') 

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='membro_comum', 
        verbose_name='Tipo de Usuário'
    )

    is_staff = models.BooleanField(default=False, verbose_name='É da Equipe')
    is_active = models.BooleanField(default=True, verbose_name='Está Ativo')
    is_superuser = models.BooleanField(default=False, verbose_name='É Superusuário')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Data de Cadastro') 

    objects = UsuarioManager()

    USERNAME_FIELD = 'login' 
    REQUIRED_FIELDS = ['email', 'reader_name'] 

    def __str__(self):
        return self.reader_name

    def get_full_name(self):
        return self.reader_name

    def get_short_name(self):
        return self.reader_name

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        permissions = [
            ("can_cadastrar_usuario_comum", "Pode cadastrar usuário comum"),
            ("can_listar_usuario_comum", "Pode listar usuário comum"),
            ("can_atualizar_usuario", "Pode atualizar usuário"),
        ]


class Livro(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título')
    autor = models.CharField(max_length=100, verbose_name='Autor')
    ano_publicacao = models.IntegerField(verbose_name='Ano de Publicação')
    genero = models.CharField(max_length=50, verbose_name='Gênero')
    disponivel = models.BooleanField(default=True, verbose_name='Disponível para Empréstimo')
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name='Data de Registro')

    def __str__(self):
        return f"{self.titulo} por {self.autor}"

    class Meta:
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'
        permissions = [
            ("can_cadastrar_livro", "Pode cadastrar livro"),
            ("can_listar_livro", "Pode listar livro"),
            ("can_atualizar_livro", "Pode atualizar livro"),
            ("can_excluir_livro", "Pode excluir livro"), 
        ]

class Emprestimo(models.Model):
    livro = models.ForeignKey('Livro', on_delete=models.CASCADE, related_name='emprestimos',
                              verbose_name='Livro')
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='emprestimos_feitos',
                                 verbose_name='Usuário')
    data_emprestimo = models.DateTimeField(auto_now_add=True, verbose_name='Data do Empréstimo')

    data_devolucao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Devolução Real')

    data_devolucao_prevista = models.DateTimeField(null=True, blank=True, verbose_name='Data de Devolução Prevista')
    devolvido = models.BooleanField(default=False, verbose_name='Devolvido')

    def __str__(self):
        status = "Devolvido" if self.devolvido else "Ativo"
        return f"Empréstimo de '{self.livro.titulo}' para '{self.usuario.reader_name}' ({status})"

    def marcar_como_devolvido(self):
        if not self.devolvido:
            momento_devolucao_atual = timezone.now()
            horario_minimo_devolucao = self.data_emprestimo + timedelta(minutes=1)
            if momento_devolucao_atual < horario_minimo_devolucao:
                self.data_devolucao = horario_minimo_devolucao
            else:
                self.data_devolucao = momento_devolucao_atual         
            self.devolvido = True
            self.livro.disponivel = True
            self.livro.save()
            self.save()

    def calcular_multa(self):
        if self.devolvido and self.data_devolucao and self.data_devolucao_prevista:
            if self.data_devolucao > self.data_devolucao_prevista:
                dias_atraso = (self.data_devolucao.date() - self.data_devolucao_prevista.date()).days
                valor_multa_por_dia = 2 
                return dias_atraso * valor_multa_por_dia
        elif not self.devolvido and self.data_devolucao_prevista:
            hoje = timezone.now().date()
            if hoje > self.data_devolucao_prevista.date():
                dias_atraso_potencial = (hoje - self.data_devolucao_prevista.date()).days
                valor_multa_por_dia = 2
                return dias_atraso_potencial * valor_multa_por_dia
        return 0 

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-data_emprestimo']
        permissions = [
            ("can_realizar_emprestimo", "Pode realizar empréstimo"),
            ("can_realizar_devolucao", "Pode realizar devolução"),
            ("can_listar_emprestimos_vencidos", "Pode listar empréstimos vencidos"),
            ("can_reservar_livro", "Pode reservar livro"),
            ("can_cancelar_reserva", "Pode cancelar reserva"),
            ("can_editar_emprestimo", "Pode editar empréstimo"),
            ("can_listar_todos_emprestimos", "Pode listar todos os empréstimos"),
        ]