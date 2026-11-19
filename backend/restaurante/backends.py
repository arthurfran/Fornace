"""Login pelo campo login e permissões administrativas do usuário do DER."""

from django.contrib.auth.backends import ModelBackend


class UsuarioBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login = username or kwargs.get("login")
        if isinstance(login, str):
            login = login.strip().lower()
        return super().authenticate(request, username=login, password=password)

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_authenticated:
            return set()
        return user_obj.get_all_permissions(obj)

    def get_user_permissions(self, user_obj, obj=None):
        return self.get_all_permissions(user_obj, obj)

    def get_group_permissions(self, user_obj, obj=None):
        return set()

    def has_perm(self, user_obj, perm, obj=None):
        return user_obj.is_authenticated and user_obj.has_perm(perm, obj)

    def has_module_perms(self, user_obj, app_label):
        return user_obj.is_authenticated and user_obj.has_module_perms(app_label)
