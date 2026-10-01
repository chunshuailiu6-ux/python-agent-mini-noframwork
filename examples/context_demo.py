"""上下文系统使用示例。

运行方式：
    .venv\\Scripts\\python.exe examples\\context_demo.py
"""

from agent.context import ContextManager, ContextScope


def main():
    # 1. 创建上下文管理器
    ctx = ContextManager()

    # 2. 设置不同作用域的上下文
    ctx.set(ContextScope.GLOBAL, "app_name", "mini-agent")
    ctx.set(ContextScope.SESSION, "user", "Alice")
    ctx.set(ContextScope.SESSION, "role", "admin")
    ctx.set(ContextScope.TEMP, "request_id", "req-001")

    # 3. 获取值
    print("app_name:", ctx.get("app_name"))
    print("user:", ctx.get("user"))
    print("missing_key:", ctx.get("missing_key", default="默认值"))

    # 4. 按作用域查询
    print("\n=== SESSION 作用域 ===")
    print(ctx.get_by_scope(ContextScope.SESSION))

    print("\n=== GLOBAL 作用域 ===")
    print(ctx.get_by_scope("global"))

    # 5. 判断存在 & 长度
    print("\n=== 基本信息 ===")
    print("has user:", ctx.has("user"))
    print("len:", len(ctx))
    print("keys:", ctx.keys())

    # 6. TTL 过期示例
    print("\n=== TTL 过期示例 ===")
    ctx.set(ContextScope.SESSION, "temp_data", "1秒后过期", ttl=1)
    print("刚设置:", ctx.get("temp_data"))
    import time
    time.sleep(1.1)
    print("1.1秒后:", ctx.get("temp_data"))  # None，已过期

    # 7. 序列化 & 反序列化
    print("\n=== 序列化 ===")
    data = ctx.serialize()
    print("JSON 字符串前100字符:", data[:100], "...")

    ctx2 = ContextManager()
    ctx2.deserialize(data)
    print("反序列化后 user:", ctx2.get("user"))
    print("反序列化后 app_name:", ctx2.get("app_name"))

    # 8. 删除 & 清空
    print("\n=== 删除 & 清空 ===")
    ctx.delete("role")
    print("删除 role 后 has:", ctx.has("role"))
    ctx.clear(ContextScope.TEMP)
    print("清空 TEMP 后 len:", len(ctx))


if __name__ == "__main__":
    main()
