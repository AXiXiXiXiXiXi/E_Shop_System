from django.apps import AppConfig


class LostfoundConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lostfound'
    
    def ready(self):
        """
        当应用准备就绪时，导入信号处理器
        这样可以确保信号在应用启动时被注册
        """
        import lostfound.signals  # noqa