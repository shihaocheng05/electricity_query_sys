# 通用工具（日期格式化、数据加密）
import jwt
from ..middleware import BusinessException
from flask import request
from pydantic import ValidationError
from functools import wraps

#jwt工具
def generate_jwt(payload:dict,secret_key):
    token=jwt.encode(
        payload,
        secret_key,
        algorithm="HS256"
    )
    return token

def verify_jwt(token,secret_key):
    if not token:
        raise BusinessException("token不能为空！",401)
    try:
        return jwt.decode(token,secret_key,algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise BusinessException(f"token校验失败，{str(e)}",401)
    except (TypeError, ValueError):
        raise BusinessException("Token格式非法", code=401)
    
#pydantic工具
#统一参数校验，可以直接在api层加入装饰器
#唯一参数：传入相应的pydantic模型
def validate_request(model):                                                    #装饰器工厂模式
    def decoration(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            try:
                if request.method=="GET":
                    # 将ImmutableMultiDict转换为普通字典
                    params = request.args.to_dict()
                    validate_data=model(**params).model_dump()            #直接用解包后的值
                elif request.method in ["POST", "PUT", "DELETE"]:
                    validate_data=model(**request.get_json()).model_dump()

                request.validate_data=validate_data
                return func(*args,**kwargs)
            
            except ValidationError as e:
                error_list=e.errors()
                err_msg=";".join([
                    f"{err['loc'][0]}:{err['msg']}" for err in error_list
                ])
                raise BusinessException(err_msg, 400)
        return wrapper
    return decoration