from django.contrib import admin
from django.urls import path
from .views import * 

urlpatterns = [
    path('', pagina_inicial, name='pagina_inicial'),
    path('home/', pagina_inicial, name='home_page'),
    path('usuario/', usuario, name='usuarios_page'),
    path('save/', salvar_nome, name='salvar_nome_page'),
    path('usuario/add/', salvar_usuario, name='salvar_usuario'),
    path('books/', books, name='books_page'),
    path('emprestimos/', realizar_emprestimo, name='emprestimos_page'), 
    path('emprestimo/', realizar_emprestimo, name='realizar_emprestimo'), 
    path('salvar_usuario/',salvar_usuario, name='salvar_usuario'), 
    path('books/add/', salvar_livro, name='salvar_livro'),
    path('emprestimos/pesquisar/', pesquisar_emprestimos, name='pesquisar_emprestimos'),
    path('emprestimos/<int:emprestimo_id>/devolver/', devolver_emprestimo, name='devolver_emprestimo'),
    path('devolucao/', devolucao_page, name='devolucao_page'), 
    path('emprestimo/devolver/<int:emprestimo_id>/', devolver_emprestimo, name='devolver_emprestimo'), 
    path('devolver_emprestimo/<int:emprestimo_id>/',devolver_emprestimo, name='devolver_emprestimo'), 
    path('emprestimo/<int:emprestimo_id>/', devolver_emprestimo, name='detalhe_emprestimo'),
    path('usuario/edit/<int:usuario_id>/', editar_usuario, name='editar_usuario'),
    path('usuario/excluir/<int:usuario_id>/', excluir_usuario, name='excluir_usuario'),
    path('books/edit/<int:livro_id>/', editar_livro, name='editar_livro'),
    path('books/delete/<int:livro_id>/', excluir_livro, name='excluir_livro'),
    path('emprestimos/editar/<int:emprestimo_id>/', editar_emprestimo, name='editar_emprestimo'),
    path('register/',user_register, name='register_page'),
    path('login/', user_login, name='login_page'), 
    path('logout/',user_logout, name='logout_page'), 
]