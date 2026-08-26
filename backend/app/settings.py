"""路径常量定义。

所有文件路径统一基于 DATA_ROOT，禁止散落硬编码路径。
"""
from pathlib import Path

# 项目根（backend/ 的上一级）
PROJECT_DIR = Path(__file__).resolve().parent.parent

# 后端目录
BACKEND_DIR = PROJECT_DIR / "backend"

# 单功能应用 worker 脚本目录
APPS_DIR = BACKEND_DIR / "apps"

# 数据根目录（DATA_ROOT）
DATA_ROOT = BACKEND_DIR / "data"

# 系统配置文件
CONFIG_PATH = DATA_ROOT / "config.json"

# 运行与输出子目录
RUNTIME_APPS_DIR = DATA_ROOT / "runtime" / "apps"
RUNTIME_FORUM_DIR = DATA_ROOT / "runtime" / "forum"
RUNTIME_FORUM_HISTORY_DIR = RUNTIME_FORUM_DIR / "history"
REPORTS_DIR = DATA_ROOT / "reports"
GRAPHS_DIR = DATA_ROOT / "graphs"
OUTPUTS_DIR = DATA_ROOT / "outputs"

# 论坛日志文件
FORUM_LATEST_LOG = RUNTIME_FORUM_DIR / "latest.log"

# 数据初始化时需要确保存在的目录（含必要子目录）
REQUIRED_DIRS = (
    RUNTIME_APPS_DIR,
    RUNTIME_FORUM_DIR,
    RUNTIME_FORUM_HISTORY_DIR,
    REPORTS_DIR,
    GRAPHS_DIR,
    OUTPUTS_DIR,
)
