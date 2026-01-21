#!/usr/bin/env python3
"""
QuantumultX 配置生成脚本（青龙面板环境变量版）
修复header问题，确保MITM证书格式正确
"""

import os
import requests
import re
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

# 基础路径配置（可通过环境变量覆盖）
LOCAL_CONFIG_PATH = os.getenv("QX_CONFIG_PATH", "/ql/data/config/QuantumultX.conf")
BACKUP_DIR = os.getenv("QX_BACKUP_DIR", "/ql/data/config/backup")
LOG_FILE = os.getenv("QX_LOG_FILE", "/ql/data/log/quantumultx_generator.log")
CACHE_FILE = os.getenv("QX_CACHE_FILE", "/ql/data/config/qx_config_cache.json")

# 远程配置地址
REMOTE_CONFIG_URL = os.getenv("QX_REMOTE_URL", "https://ddgksf2013.top/Profile/QuantumultX.conf")

# 环境变量前缀
ENV_VAR_PREFIX = "QX_"


class QuantumultXConfigGenerator:
    """QuantumultX 配置生成器"""

    def __init__(self):
        self.logger = self.setup_logger()
        self.config_sections = {}
        self.personal_config = {}

    def setup_logger(self):
        """设置日志"""
        import logging

        # 确保日志目录存在
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 创建logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # 避免重复添加handler
        if not logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.INFO)

            # 控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # 格式化器
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # 添加handler
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def parse_env_var_value(self, value: str):
        """解析环境变量的值，支持JSON和文本格式"""
        if not value:
            return None

        value = value.strip()

        # 尝试解析JSON
        if (value.startswith('[') and value.endswith(']')) or (value.startswith('{') and value.endswith('}')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # 解析失败，返回原始字符串
                pass

        # 如果不是JSON或者解析失败，直接返回字符串
        return value

    def load_personal_config_from_env(self) -> Dict:
        """从环境变量加载个人配置"""
        config = {
            "mitm": {},
            "rewrite_remote": [],
            "server_remote": [],
            "policies": [],
            "dns": [],
            "filter_remote": [],
            "filter_local": [],
            "rewrite_local": [],
            "custom_sections": {},
            "global_replacements": []
        }

        self.logger.info("开始从环境变量加载个人配置")

        # 读取所有以QX_开头的环境变量
        for key, value in os.environ.items():
            if not key.startswith(ENV_VAR_PREFIX):
                continue

            # 去掉前缀并转换为小写
            config_key = key[len(ENV_VAR_PREFIX):].lower()

            # 解析值
            parsed_value = self.parse_env_var_value(value)
            if parsed_value is None:
                continue

            # 根据key分类存储
            if config_key == "mitm_passphrase":
                # 直接存储字符串，确保不是列表
                if isinstance(parsed_value, list):
                    config["mitm"]["passphrase"] = parsed_value[0] if parsed_value else ""
                else:
                    config["mitm"]["passphrase"] = str(parsed_value)
                self.logger.info(f"加载MITM passphrase: {config['mitm']['passphrase'][:10]}...")
            elif config_key == "mitm_p12":
                # 直接存储字符串，确保不是列表
                if isinstance(parsed_value, list):
                    config["mitm"]["p12"] = parsed_value[0] if parsed_value else ""
                else:
                    config["mitm"]["p12"] = str(parsed_value)
                self.logger.info(f"加载MITM p12证书，长度: {len(config['mitm']['p12'])}")
            elif config_key == "rewrite_remote":
                if isinstance(parsed_value, list):
                    config["rewrite_remote"].extend(parsed_value)
                else:
                    config["rewrite_remote"].append(parsed_value)
            elif config_key == "server_remote":
                if isinstance(parsed_value, list):
                    config["server_remote"].extend(parsed_value)
                else:
                    config["server_remote"].append(parsed_value)
            elif config_key == "policies":
                if isinstance(parsed_value, list):
                    config["policies"].extend(parsed_value)
                else:
                    config["policies"].append(parsed_value)
                self.logger.info(f"添加策略组配置: {parsed_value}")
            elif config_key == "dns":
                if isinstance(parsed_value, list):
                    config["dns"].extend(parsed_value)
                else:
                    config["dns"].append(parsed_value)
            elif config_key == "filter_remote":
                if isinstance(parsed_value, list):
                    config["filter_remote"].extend(parsed_value)
                else:
                    config["filter_remote"].append(parsed_value)
            elif config_key == "filter_local":
                if isinstance(parsed_value, list):
                    config["filter_local"].extend(parsed_value)
                else:
                    config["filter_local"].append(parsed_value)
            elif config_key == "rewrite_local":
                if isinstance(parsed_value, list):
                    config["rewrite_local"].extend(parsed_value)
                else:
                    config["rewrite_local"].append(parsed_value)
            elif config_key.startswith("section_"):
                # 自定义section
                section_name = config_key[8:]  # 去掉"section_"
                config["custom_sections"][section_name] = parsed_value
                self.logger.info(f"加载自定义section: [{section_name}]")
            elif config_key.startswith("replace_"):
                # 全局替换规则
                config["global_replacements"].append(parsed_value)

        # 统计加载的配置数量
        rewrite_count = len(config["rewrite_remote"])
        server_count = len(config["server_remote"])
        policy_count = len(config["policies"])

        self.logger.info(f"配置加载完成: {rewrite_count}重写, {server_count}服务器, {policy_count}策略")

        return config

    def get_config_hash(self, content: str) -> str:
        """计算配置内容的哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get_remote_config(self, use_cache: bool = True) -> Optional[str]:
        """获取远程配置"""
        # 尝试使用缓存
        if use_cache and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # 检查缓存是否过期（24小时）
                cache_time_str = cache_data.get('timestamp', '')
                if cache_time_str:
                    try:
                        cache_time = datetime.fromisoformat(cache_time_str)
                        if (datetime.now() - cache_time).total_seconds() < 86400:
                            self.logger.info(f"使用缓存配置（保存于 {cache_time.strftime('%Y-%m-%d %H:%M:%S')}）")
                            return cache_data.get('content', '')
                    except ValueError:
                        pass  # 时间格式错误，跳过缓存
            except Exception as e:
                self.logger.warning(f"加载缓存失败: {str(e)}")

        # 从远程获取
        self.logger.info(f"开始获取远程配置: {REMOTE_CONFIG_URL}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/plain, */*'
        }

        try:
            response = requests.get(REMOTE_CONFIG_URL, headers=headers, timeout=30)
            response.raise_for_status()

            content = response.text
            if not content.strip():
                self.logger.error("获取的配置内容为空")
                return None

            self.logger.info(f"成功获取远程配置，大小: {len(content)} 字节")

            # 保存缓存
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'content': content,
                'hash': self.get_config_hash(content)
            }

            cache_dir = os.path.dirname(CACHE_FILE)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                self.logger.info("配置缓存已保存")
            except Exception as e:
                self.logger.error(f"保存缓存失败: {str(e)}")

            return content

        except requests.RequestException as e:
            self.logger.error(f"获取远程配置失败: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"处理远程配置时出错: {str(e)}")
            return None

    def parse_config_sections(self, config_content: str) -> Dict[str, str]:
        """解析配置文件的各个部分，不包含header"""
        sections = {}
        current_section = None
        content_lines = []

        lines = config_content.split('\n')
        for line in lines:
            # 检测新的section
            section_match = re.match(r'^\[([^\]]+)\]$', line.strip())
            if section_match:
                # 保存上一个section的内容
                if current_section is not None:
                    sections[current_section] = '\n'.join(content_lines).strip()
                # 开始新的section
                current_section = section_match.group(1)
                content_lines = []
                continue

            # 处理当前section的内容
            if current_section is not None:
                content_lines.append(line)

        # 保存最后一个section
        if current_section is not None and content_lines:
            sections[current_section] = '\n'.join(content_lines).strip()

        self.logger.info(f"解析到以下section: {list(sections.keys())}")

        return sections

    def backup_config(self, config_content: str, suffix: str = "") -> str:
        """备份配置文件"""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"QuantumultX_{timestamp}{suffix}.conf")

        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(config_content)

            self.logger.info(f"配置已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            self.logger.error(f"备份配置失败: {str(e)}")
            return ""

    def update_mitm_section(self, mitm_content: str) -> str:
        """更新MITM部分"""
        passphrase = self.personal_config.get("mitm", {}).get("passphrase", "")
        p12 = self.personal_config.get("mitm", {}).get("p12", "")

        # 清理passphrase和p12值，确保是字符串
        if isinstance(passphrase, list):
            passphrase = passphrase[0] if passphrase else ""
        if isinstance(p12, list):
            p12 = p12[0] if p12 else ""

        passphrase = str(passphrase).strip()
        p12 = str(p12).strip()

        if not passphrase or not p12:
            self.logger.warning("MITM证书信息不完整，跳过更新")
            return mitm_content

        self.logger.info(f"更新MITM证书，passphrase长度: {len(passphrase)}, p12长度: {len(p12)}")

        # 检查是否已存在证书配置
        has_passphrase = re.search(r'^passphrase\s*=', mitm_content, re.MULTILINE)
        has_p12 = re.search(r'^p12\s*=', mitm_content, re.MULTILINE)

        if has_passphrase and has_p12:
            # 替换现有证书
            lines = mitm_content.split('\n')
            updated_lines = []

            for line in lines:
                if line.strip().startswith('passphrase ='):
                    updated_lines.append(f'passphrase = {passphrase}')
                elif line.strip().startswith('p12 ='):
                    updated_lines.append(f'p12 = {p12}')
                else:
                    updated_lines.append(line)

            return '\n'.join(updated_lines)
        else:
            # 添加证书配置
            # 查找hostname行的位置
            lines = mitm_content.split('\n')
            result_lines = []

            for i, line in enumerate(lines):
                result_lines.append(line)
                # 在hostname行后添加证书
                if line.strip().startswith('hostname ='):
                    if not has_passphrase:
                        result_lines.append(f'passphrase = {passphrase}')
                    if not has_p12:
                        result_lines.append(f'p12 = {p12}')

            # 如果没有找到hostname，添加到末尾
            if not any('hostname =' in line for line in result_lines):
                result_lines.append(f'passphrase = {passphrase}')
                result_lines.append(f'p12 = {p12}')

            return '\n'.join(result_lines)

    def add_personal_policies_smart(self, policy_content: str) -> str:
        """智能添加个人策略组，确保static策略添加到static部分"""
        personal_policies = self.personal_config.get("policies", [])

        if not personal_policies:
            self.logger.info("没有个人策略组需要添加")
            return policy_content

        self.logger.info(f"开始添加个人策略组，共 {len(personal_policies)} 个")

        # 分割policy部分内容
        lines = policy_content.split('\n')

        # 找到注释行（以#开头的行）和url-latency-benchmark行的位置
        comment_lines = []
        static_lines = []
        benchmark_lines = []
        other_lines = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                comment_lines.append(line)
            elif line_stripped.startswith('static='):
                static_lines.append(line)
            elif line_stripped.startswith('url-latency-benchmark='):
                benchmark_lines.append(line)
            elif line_stripped:
                other_lines.append(line)

        self.logger.info(f"解析到: {len(static_lines)}个static策略, {len(benchmark_lines)}个benchmark策略, {len(comment_lines)}个注释")

        # 去重：收集已有的策略组名称
        existing_policy_names = set()
        for line in static_lines + benchmark_lines:
            # 提取策略组名称
            match = re.match(r'^(static|url-latency-benchmark)=([^,]+),', line.strip())
            if match:
                existing_policy_names.add(match.group(2).strip())

        # 添加个人策略组到static_lines（去重）
        added_count = 0
        for policy in personal_policies:
            if isinstance(policy, str):
                policy_str = policy.strip()
                # 提取策略组名称
                match = re.match(r'^static=([^,]+),', policy_str)
                if match:
                    policy_name = match.group(1).strip()
                    # 检查是否已存在
                    if policy_name in existing_policy_names:
                        self.logger.info(f"策略组已存在，跳过: {policy_name}")
                        continue

                    # 添加到static_lines
                    static_lines.append(policy_str)
                    existing_policy_names.add(policy_name)
                    added_count += 1
                    self.logger.info(f"添加策略组: {policy_name}")
                else:
                    self.logger.warning(f"策略组格式不正确: {policy_str}")

        if added_count == 0:
            self.logger.info("没有新的策略组需要添加")
            return policy_content

        # 重新组合policy部分
        # 按照原格式：static策略 -> 注释 -> url-latency-benchmark策略 -> 其他
        new_lines = []

        # 添加static策略
        new_lines.extend(static_lines)
        new_lines.append("")  # 空行分隔

        # 添加注释
        new_lines.extend(comment_lines)

        # 添加url-latency-benchmark策略
        new_lines.extend(benchmark_lines)

        # 添加其他行
        for line in other_lines:
            if line.strip():  # 跳过空行
                new_lines.append(line)

        self.logger.info(f"成功添加了 {added_count} 个策略组")

        return '\n'.join(new_lines)

    def add_config_items(self, section_content: str, new_items: List, section_type: str) -> str:
        """向指定section添加配置项（通用方法）"""
        if not new_items:
            self.logger.info(f"{section_type} 没有新项需要添加")
            return section_content

        self.logger.info(f"开始向 {section_type} 添加 {len(new_items)} 个配置项")

        # 收集已存在的配置项（用于去重）
        existing_items = set()
        lines = section_content.split('\n')

        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                existing_items.add(line.strip())

        # 添加新项（去重）
        added_count = 0
        for item in new_items:
            if isinstance(item, str):
                item_str = item.strip()
                if item_str and item_str not in existing_items:
                    lines.append(item_str)
                    existing_items.add(item_str)
                    added_count += 1
                    self.logger.info(f"添加 {section_type} 配置项: {item_str[:100]}")

        if added_count > 0:
            self.logger.info(f"成功向 {section_type} 添加了 {added_count} 个新项")
        else:
            self.logger.info(f"{section_type} 所有配置项已存在，无需添加")

        return '\n'.join(lines)

    def apply_global_replacements(self, config_content: str) -> str:
        """应用全局替换规则"""
        replacements = self.personal_config.get("global_replacements", [])

        if not replacements:
            return config_content

        result = config_content
        for replacement in replacements:
            if isinstance(replacement, dict) and "search" in replacement and "replace" in replacement:
                search_pattern = replacement["search"]
                replace_with = replacement["replace"]
                count = result.count(search_pattern)
                if count > 0:
                    result = result.replace(search_pattern, replace_with)
                    self.logger.info(f"全局替换: '{search_pattern}' -> '{replace_with}' (共{count}处)")

        return result

    def generate_final_config(self, sections: Dict[str, str]) -> str:
        """生成最终配置文件"""
        config_parts = []

        # 添加生成信息
        config_parts.append(f"# QuantumultX 配置文件")
        config_parts.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        config_parts.append(f"# 基于: {REMOTE_CONFIG_URL}")
        config_parts.append(f"# 配置来源: 青龙面板环境变量")
        config_parts.append("")

        # 标准section的顺序
        standard_sections_order = [
            "general",
            "task_local",
            "rewrite_local",
            "rewrite_remote",
            "server_local",
            "server_remote",
            "dns",
            "policy",
            "filter_remote",
            "filter_local",
            "http_backend",
            "mitm"
        ]

        self.logger.info(f"开始生成最终配置，标准section顺序: {standard_sections_order}")

        # 处理标准section
        for section_name in standard_sections_order:
            self.logger.info(f"处理section: [{section_name}]")

            # 获取原配置内容，如果没有则使用空字符串
            content = sections.get(section_name, "")

            # 根据不同section类型添加个人配置
            if section_name == "mitm":
                content = self.update_mitm_section(content)
                self.logger.info(f"更新MITM部分完成")
            elif section_name == "rewrite_remote":
                personal_items = self.personal_config.get("rewrite_remote", [])
                content = self.add_config_items(content, personal_items, "rewrite_remote")
            elif section_name == "rewrite_local":
                personal_items = self.personal_config.get("rewrite_local", [])
                content = self.add_config_items(content, personal_items, "rewrite_local")
            elif section_name == "server_remote":
                personal_items = self.personal_config.get("server_remote", [])
                content = self.add_config_items(content, personal_items, "server_remote")
            elif section_name == "policy":
                # 特殊处理policy部分，确保static策略添加到正确位置
                content = self.add_personal_policies_smart(content)
            elif section_name == "dns":
                personal_items = self.personal_config.get("dns", [])
                content = self.add_config_items(content, personal_items, "dns")
            elif section_name == "filter_remote":
                personal_items = self.personal_config.get("filter_remote", [])
                content = self.add_config_items(content, personal_items, "filter_remote")
            elif section_name == "filter_local":
                personal_items = self.personal_config.get("filter_local", [])
                content = self.add_config_items(content, personal_items, "filter_local")

            # 添加section到配置
            config_parts.append(f"[{section_name}]")
            if content.strip():
                config_parts.append(content)
            config_parts.append("")  # section之间的空行

        # 添加自定义section（非标准section）
        all_sections = set(sections.keys())
        custom_sections = all_sections - set(standard_sections_order)

        for section_name in sorted(custom_sections):
            config_parts.append(f"[{section_name}]")
            content = sections[section_name]
            if content.strip():
                config_parts.append(content)
            config_parts.append("")

        # 添加完全自定义的section（从环境变量加载的）
        custom_sections_from_env = self.personal_config.get("custom_sections", {})
        for section_name, content in custom_sections_from_env.items():
            if section_name not in all_sections:  # 避免重复
                config_parts.append(f"[{section_name}]")
                if isinstance(content, list):
                    config_parts.append('\n'.join(content))
                elif isinstance(content, str):
                    config_parts.append(content)
                config_parts.append("")

        # 生成完整配置
        full_config = '\n'.join(config_parts)

        # 应用全局替换
        full_config = self.apply_global_replacements(full_config)

        self.logger.info(f"最终配置生成完成，总长度: {len(full_config)} 字节")

        return full_config

    def save_config(self, config_content: str) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            config_dir = os.path.dirname(LOCAL_CONFIG_PATH)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            # 备份原配置文件（如果存在）
            if os.path.exists(LOCAL_CONFIG_PATH):
                try:
                    with open(LOCAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                    self.backup_config(old_content, "_old")
                except Exception as e:
                    self.logger.warning(f"备份原配置失败: {str(e)}")

            # 保存新配置
            with open(LOCAL_CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(config_content)

            # 备份新配置
            self.backup_config(config_content, "_new")

            self.logger.info(f"配置文件已保存到: {LOCAL_CONFIG_PATH}")
            return True

        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            return False

    def validate_mitm_section(self, config_content: str) -> bool:
        """验证MITM部分的完整性"""
        # 提取MITM部分
        lines = config_content.split('\n')
        in_mitm_section = False
        mitm_lines = []

        for line in lines:
            if line.strip() == "[mitm]":
                in_mitm_section = True
                continue
            elif in_mitm_section and line.strip().startswith("["):
                break
            elif in_mitm_section:
                if line.strip():
                    mitm_lines.append(line.strip())

        # 检查passphrase和p12格式
        passphrase_found = False
        p12_found = False
        passphrase_line = ""
        p12_line = ""

        for line in mitm_lines:
            if line.startswith("passphrase ="):
                passphrase_found = True
                passphrase_line = line
            elif line.startswith("p12 ="):
                p12_found = True
                p12_line = line

        if not passphrase_found or not p12_found:
            self.logger.error("MITM证书信息不完整")
            return False

        # 检查格式是否正确（不应该有方括号）
        if passphrase_line.startswith("passphrase = ["):
            self.logger.error(f"passphrase格式错误，包含方括号: {passphrase_line[:50]}...")
            return False

        if p12_line.startswith("p12 = ["):
            self.logger.error(f"p12格式错误，包含方括号: {p12_line[:50]}...")
            return False

        self.logger.info("MITM证书格式正确")
        return True

    def run(self) -> bool:
        """运行配置生成器"""
        self.logger.info("=" * 60)
        self.logger.info("QuantumultX 个性化配置生成器启动")
        self.logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"远程配置URL: {REMOTE_CONFIG_URL}")
        self.logger.info(f"本地配置文件: {LOCAL_CONFIG_PATH}")
        self.logger.info("=" * 60)

        # 1. 加载个人配置
        self.personal_config = self.load_personal_config_from_env()
        policies = self.personal_config.get("policies", [])
        mitm_config = self.personal_config.get("mitm", {})

        self.logger.info(f"个人配置加载完成，策略组数量: {len(policies)}")
        self.logger.info(f"MITM配置: passphrase={mitm_config.get('passphrase', '')[:10]}..., p12长度={len(mitm_config.get('p12', ''))}")

        # 2. 获取远程配置
        remote_content = self.get_remote_config(use_cache=True)
        if not remote_content:
            self.logger.error("获取远程配置失败，程序退出")
            return False

        # 3. 解析配置sections（不包含header）
        sections = self.parse_config_sections(remote_content)
        self.logger.info(f"解析到 {len(sections)} 个配置section")

        # 4. 生成最终配置
        final_config = self.generate_final_config(sections)

        # 5. 验证配置
        mitm_valid = self.validate_mitm_section(final_config)

        if not mitm_valid:
            self.logger.error("MITM证书验证失败")
            return False

        # 6. 保存配置
        if self.save_config(final_config):
            # 输出统计信息
            original_size = len(remote_content)
            final_size = len(final_config)

            self.logger.info("=" * 60)
            self.logger.info("配置生成成功！")
            self.logger.info(f"原始配置大小: {original_size} 字节")
            self.logger.info(f"最终配置大小: {final_size} 字节")
            self.logger.info(f"配置变化: {final_size - original_size} 字节")
            self.logger.info("=" * 60)

            # 输出个人化内容摘要
            summary = []

            if mitm_config.get("passphrase") and mitm_config.get("p12"):
                summary.append("MITM证书配置")

            for key in ["rewrite_remote", "server_remote", "policies", "dns",
                       "filter_remote", "filter_local", "rewrite_local"]:
                items = self.personal_config.get(key, [])
                if items:
                    summary.append(f"{len(items)}个{key}")

            custom_sections = self.personal_config.get("custom_sections", {})
            if custom_sections:
                summary.append(f"{len(custom_sections)}个自定义section")

            if summary:
                self.logger.info("已添加的个性化内容：")
                for item in summary:
                    self.logger.info(f"  - {item}")

            # 特别显示策略组详情
            if policies:
                self.logger.info("个人策略组详情:")
                for i, policy in enumerate(policies, 1):
                    self.logger.info(f"  {i}. {policy}")

            # 显示MITM证书格式
            mitm_lines = []
            lines = final_config.split('\n')
            in_mitm = False
            for line in lines:
                if line.strip() == "[mitm]":
                    in_mitm = True
                elif in_mitm and line.strip().startswith("["):
                    break
                elif in_mitm:
                    if line.strip().startswith("passphrase =") or line.strip().startswith("p12 ="):
                        mitm_lines.append(line.strip())

            if mitm_lines:
                self.logger.info("MITM证书格式检查:")
                for line in mitm_lines:
                    # 只显示前100个字符
                    self.logger.info(f"  {line[:100]}...")

            self.logger.info("=" * 60)
            self.logger.info("使用说明：")
            self.logger.info("1. 将生成的配置文件导入QuantumultX")
            self.logger.info("2. 在QuantumultX中安装MITM证书")
            self.logger.info("3. 重启QuantumultX使配置生效")
            self.logger.info("=" * 60)

            return True
        else:
            self.logger.error("配置生成失败")
            return False


def print_usage():
    """打印使用说明"""
    print("=" * 60)
    print("QuantumultX 配置生成器（最终修复版）")
    print("=" * 60)
    print("使用方法:")
    print("1. 在青龙面板中设置环境变量（以QX_开头）")
    print("2. 运行脚本生成个性化配置")
    print("")
    print("环境变量示例（重要：MITM证书必须是纯字符串，不是JSON格式）:")
    print("")
    print("# MITM证书配置（必需，纯字符串格式）")
    print("QX_MITM_PASSPHRASE=A24AB7DF")
    print("QX_MITM_P12=MIILuwIBAzCCC4UGCSqGSIb3DQEHAaCCC3YE...")
    print("")
    print("# 重写规则（可选，JSON格式）")
    print('QX_REWRITE_REMOTE=["https://github.com/ddgksf2013/Rewrite/raw/master/Function/EmbyPlugin.conf, tag=emby, update-interval=172800, opt-parser=false, enabled=true"]')
    print("")
    print("# 服务器订阅（可选）")
    print('QX_SERVER_REMOTE=["https://example.com/subscribe, tag=我的订阅, update-interval=86400, enabled=true"]')
    print("")
    print("# 策略组（可选，JSON数组格式）")
    print('QX_POLICIES=["static=AiInOne,香港节点, 美国节点,狮城节点, img-url=https://raw.githubusercontent.com/Orz-3/mini/master/Color/Global.png", "static=Steam, 自动选择, 台湾节点, direct, 香港节点, 日本节点, 美国节点, 狮城节点, proxy, img-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Steam.png"]')
    print("")
    print("注意：")
    print("1. MITM证书必须是纯字符串格式，不要用JSON数组格式")
    print("2. 脚本会自动将个人策略组添加到正确位置（static部分）")
    print("3. 不会包含原配置的header内容")
    print("=" * 60)


def main():
    """主函数"""
    # 检查是否显示使用说明
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        return

    # 运行配置生成器
    generator = QuantumultXConfigGenerator()
    success = generator.run()

    if success:
        print("✅ QuantumultX 配置生成成功！")
        print(f"📁 配置文件: {LOCAL_CONFIG_PATH}")
        print(f"📝 日志文件: {LOG_FILE}")
        print(f"💾 备份目录: {BACKUP_DIR}")
        print("")
        sys.exit(0)
    else:
        print("❌ QuantumultX 配置生成失败")
        print(f"🔍 请检查日志文件: {LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()