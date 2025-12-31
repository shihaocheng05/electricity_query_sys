# 全局异常处理、统一返回格式
class BusinessException(Exception):
    def __init__(self,msg,code=400):
        self.msg=msg
        self.code=code
        super().__init__(msg)