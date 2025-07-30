from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password 
from django.db.models import Q 
from django.utils import timezone
from django.http import HttpResponse 
from django.db import transaction 
from .models import Livro, Usuario, Emprestimo 
from .forms import UsuarioLoginForm, UsuarioRegistroForm, UsuarioAdminForm 
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required 


PERMISSAO_GERENCIAMENTO = ('admin', 'funcionario')
PERMISSAO_ADMIN = ('admin',)


def verificar_permissao(request, required_types, error_message):
    if request.user.tipo_usuario.lower() not in required_types:
        messages.error(request, error_message)
        return redirect('pagina_inicial')
    return None

def pagina_inicial(request):
    return render(request, "home.html", context={"current_tab": "home"})

def shopping(request):
    return HttpResponse("Bem-vindo(a) às compras")

def salvar_nome(request):
    nome = request.POST['Nome'] 
    
    print(f"Nome recebido na função salvar_nome: {nome}")
    print(f"Dados POST completos: {request.POST}")

    return render(request, "welcome.html", context={'Nome': nome})

def user_register(request):
    if request.method == 'POST':
        form = UsuarioRegistroForm(request.POST) 
        if form.is_valid():
            usuario = form.save() 
            messages.success(request, 'Registo realizado com sucesso! Inicie sessão para continuar.')
            return redirect('login_page')
        else:
            return render(request, 'register.html', {'form': form, 'current_tab': 'register'}) 
    else:
        form = UsuarioRegistroForm() 
    return render(request, 'register.html', {'form': form, 'current_tab': 'register'})

def user_login(request):
    if request.method == 'POST':
        form = UsuarioLoginForm(request.POST) 
        if form.is_valid():
            username = form.cleaned_data.get('login')
            password = form.cleaned_data.get('password') 

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user) 
                request.session['user_id'] = user.id 
                request.session['user_type'] = user.tipo_usuario
                messages.success(request, f"Bem-vindo(a), {user.reader_name}!")
                return redirect('home_page')
            else:
                messages.error(request, "Nome de utilizador ou palavra-passe inválidos.")
                return render(request, 'user_login.html', {'form': form, 'current_tab': 'login'}) 
        else:
            messages.error(request, "Por favor, corrija os erros no formulário de início de sessão.")
            return render(request, 'user_login.html', {'form': form, 'current_tab': 'login'})
    else:
        form = UsuarioLoginForm()
    
    return render(request, 'user_login.html', {'form': form, 'current_tab': 'login'})

def user_logout(request):
    auth_logout(request) 
    request.session.flush() 
    messages.info(request, "Foi desconectado(a).")
    return redirect('login_page')
    
def books(request):
    query = request.GET.get('query', '')
    
    if query:
        todos_os_livros = Livro.objects.filter(
            Q(titulo__icontains=query) | Q(autor__icontains=query)
        )
    else:
        todos_os_livros = Livro.objects.all()

    return render(request, "books.html",
                    context={
                        "current_tab": "books",
                        "livros": todos_os_livros,
                        "query": query
                    })

@login_required 
def usuario(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")

    form = UsuarioAdminForm(request_user=request.user) 
    query = request.GET.get('query') 
    
    todos_os_usuarios = Usuario.objects.all()
    if query:
        todos_os_usuarios = todos_os_usuarios.filter(
            Q(reader_name__icontains=query) |
            Q(reader_contact__icontains=query) |
            Q(login__icontains=query) |
            Q(email__icontains=query) 
        ).distinct() 

    can_delete_users = False
    if request.user.is_superuser:
        can_delete_users = True
    elif request.user.tipo_usuario == 'admin':   
        can_delete_users = False

    context = {
        "current_tab": "usuario", 
        "usuarios": todos_os_usuarios,
        "query": query if query else "",
        "form": form 
    }
    
    return render(request, "usuario.html", context=context)

@login_required 
def salvar_usuario(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")
    
    if request.method == "POST":
        form = UsuarioAdminForm(request.POST, request_user=request.user) 
        if form.is_valid():
            try:
                usuario = form.save() 
                messages.success(request, f"Utilizador '{usuario.reader_name}' salvo com sucesso!")
                return redirect('usuarios_page') 
            except Exception as e:
                messages.error(request, f"Ocorreu um erro inesperado ao salvar o utilizador: {e}")
        else:
            messages.error(request, "Erro ao adicionar utilizador. Por favor, corrija os erros no formulário.")
            return redirect('usuarios_page') 
    
    return redirect('usuarios_page')
    
@login_required 
def salvar_livro(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO)
        
    if request.method == "POST":
        titulo = request.POST.get('titulo') 
        autor = request.POST.get('autor')
        ano_publicacao_str = request.POST.get('ano_publicacao') 
        genero = request.POST.get('genero')

        if not titulo or not autor:
            messages.error(request, "Título e autor do livro são obrigatórios.")
            return redirect('books_page')

        ano_publicacao = None
        if ano_publicacao_str:
            try:
                ano_publicacao = int(ano_publicacao_str) 
            except ValueError:
                messages.error(request, "Ano de Publicação deve ser um número válido.")
                return redirect('books_page')

        try:
            Livro.objects.create(
                titulo=titulo,
                autor=autor,
                ano_publicacao=ano_publicacao,
                genero=genero,
                disponivel=True 
            )
            messages.success(request, f"Livro '{titulo}' de {autor} salvo com sucesso!")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao salvar o livro: {e}")

    return redirect('books_page')
    
@login_required 
def realizar_emprestimo(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")

    def render_emprestimo_page(request, error_message=None):
        if error_message:
            messages.error(request, error_message)
        livros_disponiveis = Livro.objects.filter(disponivel=True).order_by('titulo')
        usuarios_ativos = Usuario.objects.all().order_by('reader_name')
        emprestimos_ativos = Emprestimo.objects.filter(devolvido=False).order_by('data_emprestimo') 
        return render(request, 'emprestimo.html', {
            'livros': livros_disponiveis,
            'usuarios': usuarios_ativos,
            'emprestimos_ativos': emprestimos_ativos,
            'current_tab': 'emprestimo',
        })

    if request.method == 'POST':
        livro_id = request.POST.get('livro_id')
        usuario_id = request.POST.get('usuario_id')
        
        if not livro_id or not usuario_id:
            return render_emprestimo_page(request, "Por favor, selecione um livro e um usuário.")

        try:
            livro = get_object_or_404(Livro, id=livro_id)
            usuario = get_object_or_404(Usuario, id=usuario_id)

            with transaction.atomic():
                if not livro.disponivel:
                    return render_emprestimo_page(request, f"O livro '{livro.titulo}' não está disponível para empréstimo.")
                
                data_emprestimo_atual = timezone.now()
                data_devolucao_prevista_calc = data_emprestimo_atual + timedelta(days=7)

                Emprestimo.objects.create(
                    livro=livro,
                    usuario=usuario,
                    data_emprestimo=data_emprestimo_atual,
                    data_devolucao_prevista=data_devolucao_prevista_calc,
                    devolvido=False
                )
                
                livro.disponivel = False
                livro.save()
                messages.success(request, f"Livro '{livro.titulo}' emprestado com sucesso para '{usuario.reader_name}'. Data de devolução prevista: {data_devolucao_prevista_calc.strftime('%d/%m/%Y %H:%M')}")
                return redirect('realizar_emprestimo') 

        except Exception as e:
            return render_emprestimo_page(request, f"Ocorreu um erro ao realizar o empréstimo: {e}")
    
    return render_emprestimo_page(request)


@login_required 
def pesquisar_emprestimos(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")
        
    query = request.GET.get('query')
    emprestimos_ativos = Emprestimo.objects.filter(devolvido=False)

    if query:
        emprestimos_ativos = emprestimos_ativos.filter(
            Q(livro__titulo__icontains=query) |
            Q(livro__autor__icontains=query) |
            Q(usuario__reader_name__icontains=query) |
            Q(usuario__reader_contact__icontains=query)
        ).distinct()

    emprestimos_ativos = emprestimos_ativos.order_by('-data_emprestimo')

    context = {
        'livros': Livro.objects.filter(disponivel=True),
        'usuarios': Usuario.objects.all(),
        'emprestimos_ativos': emprestimos_ativos,
        'query': query,
        'current_tab': 'emprestimo'
    }

    return render(request, 'emprestimo.html', context)

@login_required 
def devolver_emprestimo(request, emprestimo_id):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, ):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, )
        
    if request.method == 'POST':
        emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id)
        if not emprestimo.devolvido:
            emprestimo.marcar_como_devolvido() 
            messages.success(request, f"Livro '{emprestimo.livro.titulo}' devolvido com sucesso por {emprestimo.usuario.reader_name}.")
        else:
            messages.info(request, "Este empréstimo já foi marcado como devolvido.")
        
    return redirect('devolucao_page') 

@login_required 
def devolucao_page(request):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")
        
    query = request.GET.get('query')

    emprestimos_devolvidos = Emprestimo.objects.filter(devolvido=True).select_related('livro', 'usuario')

    if query:
        emprestimos_devolvidos = emprestimos_devolvidos.filter(
            Q(livro__titulo__icontains=query) |
            Q(livro__autor__icontains=query) |
            Q(usuario__reader_name__icontains=query) |
            Q(usuario__reader_contact__icontains=query) 
        ).distinct()

    emprestimos_devolvidos = emprestimos_devolvidos.order_by('id')

    return render(request, 'devolucao.html', {
        'emprestimos_devolvidos': emprestimos_devolvidos,
        'query': query,
        'current_tab': 'devolucao'
    })

@login_required 
def editar_usuario(request, usuario_id):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO)
    
    usuario_obj = get_object_or_404(Usuario, id=usuario_id)

    if request.user.tipo_usuario.lower() == 'funcionario' and usuario_obj.tipo_usuario.lower() != 'membro_comum':
        messages.error(request, "Funcionários só podem editar membros comuns.")
        return redirect('usuarios_page')

    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario_obj, request_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilizador editado com sucesso!")
            return redirect('usuarios_page')
        else:
            messages.error(request, "Erro ao editar utilizador. Por favor, verifique os dados. " + form.errors.as_text())
    else:
        form = UsuarioAdminForm(instance=usuario_obj, request_user=request.user)

    return render(request, 'editar_usuario.html', {
        'usuario': usuario_obj,
        'form': form,
        'current_tab': 'usuarios'
    })

@login_required 
def excluir_usuario(request, usuario_id):
    if verificar_permissao(request, PERMISSAO_ADMIN, "Apenas administradores podem excluir usuários."):
        return verificar_permissao(request, PERMISSAO_ADMIN, "Apenas administradores podem excluir usuários.")
        
    usuario_a_excluir = get_object_or_404(Usuario, id=usuario_id)

    if request.user.id == usuario_a_excluir.id:
        messages.error(request, "Não pode excluir a sua própria conta de administrador.")
        return redirect('usuarios_page')

    if request.method == 'POST':
        try:
            nome_usuario = usuario_a_excluir.reader_name
            usuario_a_excluir.delete()
            messages.success(request, f"Utilizador '{nome_usuario}' excluído com sucesso!")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao excluir o utilizador: {e}")
    
    return redirect('usuarios_page')

@login_required 
def editar_livro(request, livro_id):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO)
        
    livro_a_editar = get_object_or_404(Livro, id=livro_id)

    if request.method == 'POST':
        try:
            livro_a_editar.titulo = request.POST.get('titulo')
            livro_a_editar.autor = request.POST.get('autor')
            
            ano_publicacao_str = request.POST.get('ano_publicacao')
            livro_a_editar.ano_publicacao = int(ano_publicacao_str) if ano_publicacao_str else None 
            livro_a_editar.genero = request.POST.get('genero')
            livro_a_editar.disponivel = request.POST.get('disponivel') == 'True'

            livro_a_editar.save()
            messages.success(request, f"Livro '{livro_a_editar.titulo}' atualizado com sucesso!")
        except ValueError:
            messages.error(request, "Erro: O 'Ano de Publicação' deve ser um número válido.")
        except Exception as e:
            messages.error(request, f"Erro inesperado ao atualizar livro: {e}")
            
        return redirect('books_page')
    
    return render(request, 'editar_livro.html', {'livro': livro_a_editar})

@login_required
def excluir_livro(request, livro_id):
    if verificar_permissao(request, PERMISSAO_ADMIN, "Apenas administradores podem excluir livros."):
        return verificar_permissao(request, PERMISSAO_ADMIN, "Apenas administradores podem excluir livros.")
        
    livro_a_excluir = get_object_or_404(Livro, id=livro_id)

    if request.method == 'POST':
        try:
            titulo_livro = livro_a_excluir.titulo 
            livro_a_excluir.delete()
            messages.success(request, f"Livro '{titulo_livro}' excluído com sucesso!")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao excluir o livro: {e}")

    return redirect('books_page') 

@login_required 
def editar_emprestimo(request, emprestimo_id):
    if verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página."):
        return verificar_permissao(request, PERMISSAO_GERENCIAMENTO, "Não tem permissão para aceder a esta página.")
        
    emprestimo_a_editar = get_object_or_404(Emprestimo, id=emprestimo_id)

    if request.method == 'POST':
        try:
            livro_id = request.POST.get('livro_id')
            usuario_id = request.POST.get('usuario_id')
            devolvido_str = request.POST.get('devolvido')

            emprestimo_a_editar.livro = get_object_or_404(Livro, id=livro_id)
            emprestimo_a_editar.usuario = get_object_or_404(Usuario, id=usuario_id)
            emprestimo_a_editar.devolvido = devolvido_str == 'True'

            if emprestimo_a_editar.devolvido and not emprestimo_a_editar.data_devolucao:
                emprestimo_a_editar.data_devolucao = timezone.now()

            emprestimo_a_editar.save()
            messages.success(request, f"Empréstimo (ID: {emprestimo_a_editar.id}) atualizado com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar empréstimo: {e}")
        
        return redirect('emprestimos_page')
    
    context = {
        'emprestimo': emprestimo_a_editar,
        'livros': Livro.objects.filter(Q(disponivel=True) | Q(id=emprestimo_a_editar.livro.id)),
        'usuarios': Usuario.objects.all(),
        'current_tab': 'emprestimo',
    }
    return render(request, 'editar_emprestimo.html', context)