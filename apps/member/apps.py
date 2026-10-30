from django.apps import AppConfig

class MemberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.member'
    
    def ready(self):
        """
        应用准备就绪时导入信号处理器
        """
        import apps.member.signals  # 导入信号模块