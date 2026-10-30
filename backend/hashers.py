from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class PlaintextPasswordHasher(BasePasswordHasher):
    """
    处理以plaintext$开头的明文密码
    """
    algorithm = "plaintext"
    
    def encode(self, password, salt=None):
        """
        创建一个哈希字符串，格式为：plaintext$password
        """
        return f"plaintext${password}"
    
    def verify(self, password, encoded):
        """
        验证密码是否匹配
        处理多种可能的格式:
        1. plaintext$password
        2. password (没有前缀)
        """
        try:
            if '$' in encoded:
                algorithm, encoded_password = encoded.split('$', 1)
                if algorithm == self.algorithm:
                    return constant_time_compare(password, encoded_password)
            
            # 如果没有前缀或格式不正确，直接比较
            return constant_time_compare(password, encoded)
        except Exception as e:
            print(f"密码验证错误: {e}, 尝试直接比较")
            return constant_time_compare(password, encoded)
    
    def safe_summary(self, encoded):
        """
        返回一个摘要，用于在管理界面显示
        """
        try:
            if '$' in encoded:
                algorithm, encoded_password = encoded.split('$', 1)
                return {
                    'algorithm': algorithm,
                    'hash': '******',
                }
            return {
                'algorithm': 'unknown',
                'hash': '******',
            }
        except Exception:
            return {
                'algorithm': 'unknown',
                'hash': '******',
            }
    
    def harden_runtime(self, password, encoded):
        """
        不做任何处理
        """
        pass