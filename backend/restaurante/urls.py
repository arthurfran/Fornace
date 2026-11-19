from django.urls import path
from . import views as v

urlpatterns = [
    path("contexto/", v.ContextoView.as_view()),
    path("login/", v.LoginView.as_view()),
    path("cadastro/", v.CadastroView.as_view()),
    path("logout/", v.LogoutView.as_view()),
    path("cardapio/", v.CardapioView.as_view()),
    path("carrinhos/<str:origem>/", v.CarrinhoView.as_view()),
    path("carrinhos/<str:origem>/confirmar/", v.ConfirmacaoView.as_view()),
    path("pedidos/", v.PedidosView.as_view()),
    path("itens/<int:item_id>/preparo/", v.PreparoView.as_view()),
    path("pedidos/<int:pedido_id>/entregar/", v.EntregaView.as_view()),
    path("escala/", v.EscalaView.as_view()),
    path("cardapio/<int:item_id>/disponibilidade/", v.DisponibilidadeView.as_view()),
    path("usuarios/", v.UsuariosView.as_view()),
    path("usuarios/<int:user_id>/", v.UsuarioView.as_view()),
    path("analise/", v.AnaliseView.as_view()),
    path("saude/", v.SaudeView.as_view()),
]
