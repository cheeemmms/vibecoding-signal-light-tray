@echo off
REM Claude Code hook 脚本 - 写入会话状态到 signal-light-tray
REM 由 signal-light-tray 安装到 Claude Code settings.json 的 hooks 配置中

cd /d "%~dp0.."
python -m signal_light_tray.claude_code_hook
