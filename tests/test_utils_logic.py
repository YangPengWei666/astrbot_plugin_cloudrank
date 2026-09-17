# -*- coding: utf-8 -*-
"""
cloudrank 修复逻辑隔离测试（#23 修复验证）
不依赖真实 AstrBot 环境，mock 掉 astrbot/jieba 依赖，仅验证核心逻辑。
运行: python3 tests/test_utils_logic.py
"""
import sys
import types
import importlib.util

# ---------- mock 外部依赖 ----------
_jieba = types.ModuleType("jieba")
_jieba.lcut = lambda s: list(s)
_jieba.cut = lambda s: list(s)
sys.modules["jieba"] = _jieba

_astrbot = types.ModuleType("astrbot")
_api = types.ModuleType("astrbot.api")
_logger = types.ModuleType("astrbot.api.logger")
_logger.info = _logger.warning = _logger.error = _logger.debug = lambda *a, **k: None
_star = types.ModuleType("astrbot.api.star")
_star.StarTools = object
_api.logger = _logger
_api.star = _star
_astrbot.api = _api
sys.modules["astrbot"] = _astrbot
sys.modules["astrbot.api"] = _api
sys.modules["astrbot.api.logger"] = _logger
sys.modules["astrbot.api.star"] = _star

# ---------- 加载插件模块（模拟包结构） ----------
BASE = "/home/user/plugin-dev/astrbot_plugin_cloudrank"


def load_pkg(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


constant = load_pkg("cr.constant", f"{BASE}/constant.py")
utils = load_pkg("cr.utils", f"{BASE}/utils.py")

# ---------- 测试 ----------
passed = 0
failed = 0


def check(name, got, expected):
    global passed, failed
    ok = got == expected
    if ok:
        passed += 1
        print(f"  ✅ {name}: {got!r}")
    else:
        failed += 1
        print(f"  ❌ {name}: 期望 {expected!r}, 实际 {got!r}")


print("== extract_group_id_from_session（修复后 main.py 使用的同步函数）==")
check("三段式QQ群", utils.extract_group_id_from_session("aiocqhttp:GroupMessage:123456789"), "123456789")
check("带0_前缀群号", utils.extract_group_id_from_session("aiocqhttp:GroupMessage:0_123456789"), "123456789")
check("下划线格式", utils.extract_group_id_from_session("aiocqhttp_group_142443871"), "142443871")
check("微信chatroom", utils.extract_group_id_from_session("wechatpadpro_group_123456789@chatroom"), "123456789@chatroom")
check("纯数字群号", utils.extract_group_id_from_session("123456789"), "123456789")
check("私聊会话返回None", utils.extract_group_id_from_session("aiocqhttp:PrivateMessage:user123"), None)
check("空串返回None", utils.extract_group_id_from_session(""), None)
check("None返回None", utils.extract_group_id_from_session(None), None)

print("\n== is_group_enabled ==")
check("已启用群", utils.is_group_enabled("123456789", {"123456789"}), True)
check("未启用群", utils.is_group_enabled("987654321", {"123456789"}), False)
check("空列表=全部不启用", utils.is_group_enabled("123456789", set()), False)
check("int群号可转换", utils.is_group_enabled(123456789, {"123456789"}), True)
check("coroutine对象(修复前bug场景)不误判", utils.is_group_enabled(object(), {"123456789"}), False)

print("\n== parse_group_list ==")
check("逗号分隔", utils.parse_group_list("111, 222,333"), {"111", "222", "333"})
check("空串", utils.parse_group_list(""), set())
check("None", utils.parse_group_list(None), set())

print(f"\n结果: {passed} 通过, {failed} 失败")
sys.exit(1 if failed else 0)
