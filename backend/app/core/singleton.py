"""
单例装饰器
用于将 Service 类转换为单例模式
"""


def singleton(cls):
    """
    单例装饰器
    
    将一个类转换为单例模式。第一次创建实例时会初始化，
    后续调用将返回同一个实例。
    
    使用方式：
    @singleton
    class MyService:
        def __init__(self):
            self.data = []
    
    service1 = MyService()  # 创建实例
    service2 = MyService()  # 返回同一个实例
    assert service1 is service2  # True
    """
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance
