"""
rt_cli/cli.py - Root 命令行分发系统

通过 python -m rt_cli <命令> 或 rt <命令> 调用
"""
import os, sys, subprocess, argparse, textwrap

# Windows GBK 终端兼容
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "gb2312"):
    sys.stdout.reconfigure(errors="replace") if hasattr(sys.stdout, "reconfigure") else None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def _frontends():
    return os.path.join(PROJECT_DIR, "frontends")

def _reflect():
    return os.path.join(PROJECT_DIR, "reflect")


def launch_frontend(cmd_parts, args=None):
    """启动前端/工具进程"""
    full_cmd = []
    for part in cmd_parts:
        part = part.replace("{PROJECT_DIR}", PROJECT_DIR)
        part = part.replace("{FRONTENDS}", _frontends())
        part = part.replace("{REFLECT}", _reflect())
        full_cmd.append(part)

    # 插入额外参数
    if args:
        full_cmd.extend(args)

    # Preserve the user's invocation directory for frontends that need it
    # (e.g. TUI's @file picker). Bash/cmd wrappers may have already set this;
    # otherwise capture the current cwd before we chdir into PROJECT_DIR.
    env = os.environ.copy()
    env.setdefault("RT_SESSION_CWD", os.getcwd())

    print(f"🚀 {' '.join(full_cmd)}")
    sys.stdout.flush()
    os.chdir(PROJECT_DIR)
    proc = subprocess.Popen(full_cmd, env=env)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)


COMMANDS = {
    "gui": {
        "help": "启动桌面GUI (qtapp)",
        "desc": "启动基于 PyQt5 的完整桌面聊天界面（气泡代码高亮、文件拖拽、历史搜索）",
        "cmd": ["python", "{FRONTENDS}/qtapp.py"],
    },
    "configure": {
        "help": "运行初始配置向导 (configure_mykey.py)",
        "desc": "首次安装后配置 API Key、模型参数等基础设置",
        "cmd": ["python", "{PROJECT_DIR}/assets/configure_mykey.py"],
    },
    "hub": {
        "help": "启动 Hub 管理器 (launcher)",
        "desc": "启动 hub 前端管理面板（系统托盘 + 浏览器界面）",
        "cmd": ["python", "{PROJECT_DIR}/hub.pyw"],
    },
    "tui": {
        "help": "启动新版终端 TUI (tui_v3)",
        "desc": "启动新版滚屏式终端界面 (tui_v3，scrollback-first，单文件实现)，纯终端/SSH 推荐",
        "cmd": ["python", "{FRONTENDS}/tui_v3.py"],
    },
    "tui-v3": {
        "help": "启动新版终端 TUI (tui_v3，显式别名)",
        "desc": "等同于 rt tui，指向 frontends/tui_v3.py",
        "cmd": ["python", "{FRONTENDS}/tui_v3.py"],
    },
    "tui-v2": {
        "help": "启动 Textual 终端 TUI v2 (tuiapp_v2)",
        "desc": "启动 Textual v2 终端图形界面（含 /btw /continue /export /restore）",
        "cmd": ["python", "{FRONTENDS}/tuiapp_v2.py"],
    },
    "tui2": {
        "help": "启动 Textual 终端 TUI v2 (tuiapp_v2，旧别名)",
        "desc": "等同于 rt tui-v2，保留以兼容旧用法",
        "cmd": ["python", "{FRONTENDS}/tuiapp_v2.py"],
    },
    "tui-legacy": {
        "help": "启动旧版终端 TUI (tuiapp)",
        "desc": "启动旧版 Textual TUI（保留用于回退/调试）",
        "cmd": ["python", "{FRONTENDS}/tuiapp.py"],
    },
    "cli": {
        "help": "启动 CLI 对话 (agentmain)",
        "desc": "启动命令行交互对话模式，最轻量的使用方式",
        "cmd": ["python", "{PROJECT_DIR}/agentmain.py"],
    },
    "launch": {
        "help": "启动 webview 桌面壳 (launch.pyw)",
        "desc": "以原生窗口形式包装 stapp Web 界面（基于 pywebview）",
        "cmd": ["python", "{PROJECT_DIR}/launch.pyw"],
    },
    "status": {
        "help": "检查运行状态",
        "desc": "检查当前是否已有 Root 进程在运行",
        "cmd": None,
        "internal": True,
    },
    "update": {
        "help": "更新项目 (git pull + pip install)",
        "desc": "从 Git 拉取最新代码并更新依赖",
        "cmd": None,
        "internal": True,
    },
    "list": {
        "help": "列出所有可用前端/服务",
        "desc": "显示所有注册的命令",
        "cmd": None,
        "internal": True,
    },
}


def cmd_list():
    """展示所有可用命令"""
    print()
    frontend_cmds = [(k, v) for k, v in sorted(COMMANDS.items()) if v["cmd"] is not None]
    internal_cmds = [(k, v) for k, v in sorted(COMMANDS.items()) if v["cmd"] is None]

    print(f"  {'命令':20s}  {'说明'}")
    print(f"  {'━'*20}  {'━'*40}")
    for name, info in frontend_cmds:
        print(f"  {name:20s}  {info.get('help', info['desc'][:40])}")
    print()
    for name, info in internal_cmds:
        print(f"  {name:20s}  {info.get('help', info['desc'][:40])}")
    print()


def cmd_status():
    """检查进程状态"""
    import psutil
    running = [p for p in psutil.process_iter(['pid', 'name', 'cmdline'])
               if p.info['cmdline'] and any('agentmain' in c for c in p.info['cmdline'])]
    if running:
        print(f"🟢 运行中: {len(running)} 个进程")
        for p in running:
            print(f"   PID {p.info['pid']} — {' '.join(p.info['cmdline'][:3])}")
    else:
        print("⚫ Root 进程未运行")


def cmd_update():
    """git pull + pip install"""
    os.chdir(PROJECT_DIR)
    print("🔄 git pull...")
    r = subprocess.run(["git", "pull"], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    print("📦 pip install...")
    r2 = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."],
                        capture_output=True, text=True)
    print(r2.stdout[-500:] if r2.stdout else "")
    if r2.returncode != 0:
        print(r2.stderr[-500:])


def main():
    parser = argparse.ArgumentParser(
        prog="rt",
        description="Root 全局命令入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              rt gui               启动桌面 GUI
              rt web               启动 Web 增强版
              rt web --native      启动 Web 基础版(桌面壳)
              rt tui               启动新版终端 TUI (v3, scrollback-first)
              rt tui-v2            启动 Textual v2 终端 TUI
              rt tui-legacy        启动旧版 Textual TUI
              rt pet               启动桌面宠物 v2
              rt launch            启动 webview 桌面壳
              rt list              列出所有命令
        """),
    )
    parser.add_argument("command", nargs="?", help="命令名")
    parser.add_argument("args", nargs="*", help="子命令参数")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本")

    args, unknown = parser.parse_known_args()

    if args.version:
        print("Root v0.1.0")
        return

    cmd = args.command

    if not cmd or cmd == "help":
        parser.print_help()
        print("\n--- 命令列表 ---")
        cmd_list()
        return

    if cmd == "list":
        cmd_list()
        return

    if cmd == "status":
        cmd_status()
        return

    if cmd == "update":
        cmd_update()
        return

    if cmd not in COMMANDS:
        print(f"❌ 未知命令: {cmd}")
        print(f"   使用 'rt list' 查看可用命令")
        sys.exit(1)

    info = COMMANDS[cmd]

    # 内置命令走内部逻辑
    if info.get("internal"):
        print(f"❌ 命令 {cmd} 没有配置启动命令")
        sys.exit(1)

    extra = list(args.args) + unknown

    # === 处理命令特有 flags ===
    cmd_parts = list(info["cmd"])

    # 处理 flags (如 --native)
    flags = info.get("flags", {})
    for flag_name, flag_info in flags.items():
        if flag_name in extra:
            cmd_parts = list(flag_info["cmd"])
            extra.remove(flag_name)
            break

    launch_frontend(cmd_parts, extra if extra else None)


if __name__ == "__main__":
    main()
