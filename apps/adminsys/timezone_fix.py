"""
时区问题修复工具
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import pytz

class TimezoneHelper:
    """时区帮助类"""
    
    @staticmethod
    def get_local_timezone():
        """获取本地时区"""
        return pytz.timezone(settings.TIME_ZONE)
    
    @staticmethod
    def convert_utc_to_local(utc_datetime):
        """将UTC时间转换为本地时间"""
        if utc_datetime.tzinfo is None:
            # 如果没有时区信息，假设它是UTC时间
            utc_datetime = timezone.make_aware(utc_datetime, pytz.UTC)
        
        local_tz = TimezoneHelper.get_local_timezone()
        return utc_datetime.astimezone(local_tz)
    
    @staticmethod
    def convert_local_to_utc(local_datetime):
        """将本地时间转换为UTC时间"""
        if local_datetime.tzinfo is None:
            # 如果没有时区信息，假设它是本地时间
            local_tz = TimezoneHelper.get_local_timezone()
            local_datetime = local_tz.localize(local_datetime)
        
        return local_datetime.astimezone(pytz.UTC)
    
    @staticmethod
    def now_local():
        """获取当前本地时间"""
        return timezone.localtime()
    
    @staticmethod
    def format_local_time(datetime_obj, format_str='%Y-%m-%d %H:%M:%S'):
        """格式化本地时间"""
        if datetime_obj:
            local_time = TimezoneHelper.convert_utc_to_local(datetime_obj)
            return local_time.strftime(format_str)
        return None

def fix_timezone_display():
    """修复时区显示问题的建议"""
    
    print("时区问题诊断和修复建议：\n")
    
    print("1. 当前配置检查：")
    print(f"   TIME_ZONE: {settings.TIME_ZONE}")
    print(f"   USE_TZ: {settings.USE_TZ}")
    print(f"   当前Django时区: {timezone.get_current_timezone()}")
    print(f"   当前UTC时间: {timezone.now()}")
    print(f"   当前本地时间: {timezone.localtime()}")
    
    print("\n2. 问题说明：")
    print("   Django默认将时间以UTC格式存储在数据库中，这是正确的做法。")
    print("   在显示时，需要转换为本地时间。")
    
    print("\n3. 解决方案：")
    print("   选项A: 在模板和API中使用本地时间显示")
    print("   选项B: 修改settings.py禁用时区感知（不推荐）")
    print("   选项C: 确保数据库时区设置正确")
    
    return True

if __name__ == "__main__":
    fix_timezone_display() 