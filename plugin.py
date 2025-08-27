# src/plugins/My_Fucked_100_people/plugin.py
import os
import json
import aiohttp
import random
import base64
import datetime
from typing import List, Tuple, Type, Any, Dict, Optional
from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseCommand,
    ComponentInfo,
    ConfigField
)
from src.plugin_system.apis import send_api

PLUGIN_DIR = os.path.dirname(__file__)

# --- 插件定义 ---
@register_plugin
class QQFrequencyTrackerPlugin(BasePlugin):
    """让群u去到成都"""

    plugin_name = "My_fucked_100_people"
    plugin_description = "- 群u群u，你看。- 不是你干嘛啊，快拿开"
    plugin_version = "1.3.3" # 更新版本号以反映改动
    plugin_author = "Unreal"
    enable_plugin = True
    dependencies = []
    python_dependencies = ["aiohttp"]

    config_file_name = "config.toml"
    config_section_descriptions = {
        "plugin": "插件启用配置"
    }
    config_schema = {
        "plugin": {
            "enabled": ConfigField(
                type=bool,
                default=True,
                description="是否启用插件"
            ),
            "op_list": ConfigField(
                type=list,
                default=[],
                description="CB之神列表，输入QQ号，例如 ['123456789', '987654321']"
            )
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """注册插件组件"""
        return [
            (CcbCommand.get_command_info(), CcbCommand),
            (CxCommand.get_command_info(), CxCommand),
            (RankCommand.get_command_info(), RankCommand)
        ]


# --- 工具函数 ---
def _load_json_data(filename: str) -> dict:
    """加载JSON数据文件"""
    file_path = os.path.join(PLUGIN_DIR, filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回的是字典
                if isinstance(data, dict):
                    return data
                else:
                    # 如果数据格式不正确，记录警告并返回空字典
                    # 注意：BaseCommand 中才有 self.logger，这里无法直接使用
                    # print(f"警告: {filename} 数据格式不正确，期望 dict，实际 {type(data)}") # 用于调试
                    return {}
        except (json.JSONDecodeError, Exception) as e:
            # 加载失败，记录日志并返回空字典
            # print(f"加载 {filename} 失败: {e}") # 用于调试
            return {}
    return {}

def _save_json_data(filename: str, data: dict):
    """保存JSON数据文件"""
    file_path = os.path.join(PLUGIN_DIR, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise e # 让调用者处理保存失败

# --- Command组件 ---

class CcbCommand(BaseCommand):
    """处理 /ccb <qq号> 命令"""

    command_name = "CcbCommand"
    command_description = "记录指定QQ号的出现频率和避税量。用法: /ccb <QQ号码>"
    command_pattern = r"^/ccb\s*(?P<qq>\d{5,15})$"
    command_help = "想不想C群u？用法: /ccb <QQ号码>"
    command_examples = ["/ccb 123456789"]
    intercept_message = True

    async def execute(self) -> Tuple[bool, str, bool]:
        """执行命令逻辑"""
        qq_number = self.matched_groups.get("qq")
        if not qq_number:
            try:
                await self.send_text("❌ 命令格式错误，请使用: /ccb <QQ号码>")
            except Exception as e:
                 self.logger.warning(f"发送格式错误消息失败: {e}")
            return False, "缺少QQ号参数", True

        chat_stream = getattr(self, 'chat_stream', None)
        if chat_stream is None:
            message_obj = getattr(self, 'message', None)
            if message_obj:
                chat_stream = getattr(message_obj, 'chat_stream', None)

        if chat_stream is None:
            error_msg = "❌ 无法获取聊天上下文信息 (chat_stream)。"
            self.logger.error("CcbCommand: execute 方法无法从 self 获取有效的 chat_stream。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天上下文错误消息也失败了: {send_e}")
            return False, "缺少聊天上下文 (chat_stream)", True

        stream_id = getattr(chat_stream, 'stream_id', None)
        if stream_id is None:
            error_msg = "❌ 无法获取聊天流ID (stream_id)。"
            self.logger.error("CcbCommand: execute 方法无法从 chat_stream 获取有效的 stream_id。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天流ID错误消息也失败了: {send_e}")
            return False, "缺少聊天流ID (stream_id)", True

        op_list = self.get_config("plugin.op_list", [])
        if not isinstance(op_list, list):
            op_list = []
        op_list_str = [str(op) for op in op_list]
        
        if qq_number in op_list_str:
            message_text = "哥们，这b开了（CB之神的庇护）"
            try:
                await send_api.text_to_stream(
                    text=message_text,
                    stream_id=stream_id
                )
                return True, "命中 OP 列表，已发送提示", True
            except Exception as e:
                self.logger.error(f"发送 OP 提示失败: {e}")
                return False, "发送 OP 提示失败", True

        # --- 核心逻辑 ---
        freq_data = _load_json_data("data.json")
        tax_data = _load_json_data("tax_totals.json")
        debt_data = _load_json_data("debt_info.json") # 加载怀孕信息
        deadbeat_data = _load_json_data("deadbeat_counts.json") # 加载堕胎次数

        # 确保 freq_data 和 tax_data 是字典
        if not isinstance(freq_data, dict):
            freq_data = {}
        if not isinstance(tax_data, dict):
            tax_data = {}

        # 更新频率
        initial_record = qq_number not in freq_data
        if not initial_record:
            freq_data[qq_number] = freq_data.get(qq_number, 0) + 1
        else:
            freq_data[qq_number] = 1
        frequency = freq_data[qq_number]

        # 生成并累加避税量
        ccb_amount = random.uniform(0, 114)
        if qq_number in tax_data:
            tax_data[qq_number] = tax_data.get(qq_number, 0.0) + ccb_amount
        else:
            tax_data[qq_number] = ccb_amount
        total_tax = tax_data[qq_number]

        # --- 新增逻辑：怀孕与堕胎判断 ---
        is_newly_in_debt = False
        is_deadbeat_event = False
        deadbeat_incremented = False
        debt_status_removed = False # 新增：标记是否移除了怀孕状态

        # 1. 判断是否新怀孕 (累计 > 514 且未在怀孕名单)
        if total_tax > 514 and qq_number not in debt_data:
            debt_data[qq_number] = {
                "debt_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "total_tax_at_debt": total_tax
            }
            is_newly_in_debt = True
            _save_json_data("debt_info.json", debt_data) # 立即保存怀孕信息

        # 2. 判断是否已是怀孕状态且本次避税 > 100 (堕胎事件)
        elif qq_number in debt_data and ccb_amount > 100:
            # 增加堕胎次数
            if qq_number in deadbeat_data:
                deadbeat_data[qq_number] = deadbeat_data.get(qq_number, 0) + 1
            else:
                deadbeat_data[qq_number] = 1
            
            # 重置避税总量
            tax_data[qq_number] = 0.0
            
            # *** 关键修改：移除怀孕状态 ***
            if qq_number in debt_data:
                del debt_data[qq_number]
                debt_status_removed = True
            
            is_deadbeat_event = True
            deadbeat_incremented = True
            # 保存更新后的数据
            _save_json_data("deadbeat_counts.json", deadbeat_data) # 保存堕胎次数
            _save_json_data("tax_totals.json", tax_data) # 保存重置后的避税总量
            if debt_status_removed:
                _save_json_data("debt_info.json", debt_data) # *** 保存移除怀孕状态后的数据 ***

        # --- 保存频率和避税数据 (如果未在堕胎事件中保存过) ---
        # 注意：堕胎事件中已经保存了 tax_data 和 debt_data，所以这里需要判断
        if not is_deadbeat_event: # 堕胎事件已经保存了 tax_data 和 debt_data
            _save_json_data("tax_totals.json", tax_data)
            # debt_data 也可能在新怀孕时被修改并保存了
            if is_newly_in_debt:
                pass # 已经保存过了
            elif debt_status_removed: # 如果在堕胎事件中已经保存了 debt_data
                pass
            else:
                 _save_json_data("debt_info.json", debt_data) # 以防有其他修改（虽然当前逻辑不太可能）
                 
        _save_json_data("data.json", freq_data) # 频率数据总是需要保存

        # --- 构造消息文本 ---
        debt_status_text = ""
        if is_newly_in_debt:
            debt_status_text = " [怀孕标记]"
        elif qq_number in debt_data: # 检查是否仍然怀孕（未触发堕胎）
            # 计算怀孕天数
            try:
                debt_date_str = debt_data[qq_number]["debt_date"]
                debt_date = datetime.datetime.strptime(debt_date_str, "%Y-%m-%d")
                current_date = datetime.datetime.now()
                days_in_debt = (current_date - debt_date).days
                debt_status_text = f" [怀孕{days_in_debt}天]"
            except (ValueError, KeyError):
                debt_status_text = " [怀孕状态异常]"
        # 如果 debt_status_removed 为 True，或者 qq_number 不在 debt_data 中，则不显示怀孕状态

        if is_deadbeat_event and deadbeat_incremented:
            # 根据是否移除了怀孕状态，调整提示文本
            if debt_status_removed:
                debt_status_text = " [堕胎+1，怀孕状态已移除]"
            else:
                debt_status_text = " [堕胎+1]"

        message_text = (
            f"这是 {qq_number} 的第一次，你成功拿下一血）共查出{ccb_amount:.2f}ml避税。累计避税: {total_tax:.2f}ml{debt_status_text}"
            if initial_record
            else f"这是Ta的第 {frequency} 次。共查出{ccb_amount:.2f}ml避税，真的太逊了。累计避税: {total_tax:.2f}ml{debt_status_text}"
        )

        # --- 获取头像和发送消息 ---
        avatar_base64 = None
        avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={qq_number}&s=100"
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(avatar_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        avatar_base64 = base64.b64encode(image_data).decode('utf-8')
                    else:
                        self.logger.warning(f"获取头像失败，状态码: {response.status} for QQ: {qq_number}")
        except Exception as e:
            self.logger.error(f"获取头像时发生异常 for QQ: {qq_number}: {e}")

        send_success = False
        try:
            send_success = await send_api.text_to_stream(
                text=message_text,
                stream_id=stream_id,
            )

            if not send_success:
                raise Exception("发送文本消息失败")

            avatar_send_success = True
            if avatar_base64:
                avatar_send_success = await send_api.image_to_stream(
                    image_base64=avatar_base64,
                    stream_id=stream_id
                )
                if not avatar_send_success:
                    self.logger.warning(f"发送头像失败 QQ: {qq_number}")

            final_success = send_success
            result_msg = f"成功FUCKQQ号 {qq_number}，当前FUCK {frequency}，本次避税 {ccb_amount:.2f}ml"
            if not avatar_send_success:
                 result_msg += " (头像发送失败)"
            if is_newly_in_debt:
                result_msg += " (新增怀孕)"
            if is_deadbeat_event and deadbeat_incremented:
                result_msg += " (堕胎次数+1)"
                if debt_status_removed:
                    result_msg += " (怀孕状态已移除)"

            return final_success, result_msg, True

        except Exception as e:
            error_msg = "❌ 发送消息失败，请稍后重试。"
            self.logger.error(f"发送消息时发生异常: {e}", exc_info=True)
            try:
                 await send_api.text_to_stream(
                    text=error_msg,
                    stream_id=stream_id
                )
            except Exception as send_error:
                self.logger.error(f"发送错误信息也失败了: {send_error}")
            return False, f"发送消息失败: {e}", True


class CxCommand(BaseCommand):
    """处理 /cx <qq号> 命令，查询避税总量"""

    command_name = "CxCommand"
    command_description = "查询指定QQ号的避税总量、怀孕状态和堕胎次数。用法: /cx <QQ号码>"
    command_pattern = r"^/cx\s*(?P<qq>\d{5,15})$"
    command_help = "查询避税总量：/cx <QQ号码>"
    command_examples = ["/cx 123456789"]
    intercept_message = True

    async def execute(self) -> Tuple[bool, str, bool]:
        """执行查询命令逻辑"""
        qq_number = self.matched_groups.get("qq")
        if not qq_number:
            try:
                await self.send_text("❌ 命令格式错误，请使用: /cx <QQ号码>")
            except Exception as e:
                self.logger.warning(f"发送格式错误消息失败: {e}")
            return False, "缺少QQ号参数", True

        chat_stream = getattr(self, 'chat_stream', None)
        if chat_stream is None:
            message_obj = getattr(self, 'message', None)
            if message_obj:
                chat_stream = getattr(message_obj, 'chat_stream', None)

        if chat_stream is None:
            error_msg = "❌ 无法获取聊天上下文信息 (chat_stream)。"
            self.logger.error("CxCommand: execute 方法无法从 self 获取有效的 chat_stream。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天上下文错误消息也失败了: {send_e}")
            return False, "缺少聊天上下文 (chat_stream)", True

        stream_id = getattr(chat_stream, 'stream_id', None)
        if stream_id is None:
            error_msg = "❌ 无法获取聊天流ID (stream_id)。"
            self.logger.error("CxCommand: execute 方法无法从 chat_stream 获取有效的 stream_id。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天流ID错误消息也失败了: {send_e}")
            return False, "缺少聊天流ID (stream_id)", True

        # --- 加载所有相关数据 ---
        tax_data = _load_json_data("tax_totals.json")
        freq_data = _load_json_data("data.json")
        debt_data = _load_json_data("debt_info.json")
        deadbeat_data = _load_json_data("deadbeat_counts.json")

        # 确保数据是字典
        tax_data = tax_data if isinstance(tax_data, dict) else {}
        freq_data = freq_data if isinstance(freq_data, dict) else {}
        debt_data = debt_data if isinstance(debt_data, dict) else {}
        deadbeat_data = deadbeat_data if isinstance(deadbeat_data, dict) else {}

        # --- 构造详细的回复信息 ---
        info_lines = [f"🔍 QQ号 {qq_number} 的详细信息："]

        # 1. 查询次数
        query_count = freq_data.get(qq_number, 0)
        info_lines.append(f"  • 查询次数: {query_count} 次")

        # 2. 累计避税
        total_tax = tax_data.get(qq_number, 0.0)
        info_lines.append(f"  • 累计避税: {total_tax:.2f} ml")

        # 3. 怀孕状态
        if qq_number in debt_data:
            try:
                debt_date_str = debt_data[qq_number]["debt_date"]
                debt_date = datetime.datetime.strptime(debt_date_str, "%Y-%m-%d")
                current_date = datetime.datetime.now()
                days_in_debt = (current_date - debt_date).days
                info_lines.append(f"  • 怀孕状态: 是 (自 {debt_date_str} 起怀孕 {days_in_debt} 天)")
            except (ValueError, KeyError):
                info_lines.append("  • 怀孕状态: 是 (日期信息异常)")
        else:
            info_lines.append("  • 怀孕状态: 否")

        # 4. 堕胎次数
        deadbeat_count = deadbeat_data.get(qq_number, 0)
        info_lines.append(f"  • 堕胎次数: {deadbeat_count} 次")

        message_text = "\n".join(info_lines)

        # --- 发送消息 ---
        try:
            await send_api.text_to_stream(
                text=message_text,
                stream_id=stream_id,
            )
            return True, f"成功查询QQ号 {qq_number} 的详细信息", True
        except Exception as e:
            error_msg = "❌ 发送查询结果失败，请稍后重试。"
            self.logger.error(f"发送查询结果时发生异常: {e}", exc_info=True)
            try:
                await send_api.text_to_stream(
                    text=error_msg,
                    stream_id=stream_id
                )
            except Exception as send_error:
                self.logger.error(f"发送错误信息也失败了: {send_error}")
            return False, f"发送查询结果失败: {e}", True


class RankCommand(BaseCommand):
    """处理 /rank 命令，显示排行榜"""

    command_name = "RankCommand"
    command_description = "显示避税总量和被查询次数排行榜。用法: /rank [tax|freq|help]"
    # 修改正则表达式以匹配 'help' 子命令
    command_pattern = r"^/rank(?:\s+(?P<type>tax|freq|help))?$"
    command_help = "查看排行榜：/rank [tax|freq|help] (tax: 避税榜, freq: 查询榜, help: 帮助)"
    command_examples = ["/rank", "/rank tax", "/rank freq", "/rank help"]
    intercept_message = True

    async def execute(self) -> Tuple[bool, str, bool]:
        """执行排行榜命令逻辑"""
        # 1. 解析参数
        rank_type = self.matched_groups.get("type", "all") # 默认显示所有排行榜

        # 2. 获取聊天上下文
        chat_stream = getattr(self, 'chat_stream', None)
        if chat_stream is None:
            message_obj = getattr(self, 'message', None)
            if message_obj:
                chat_stream = getattr(message_obj, 'chat_stream', None)

        if chat_stream is None:
            error_msg = "❌ 无法获取聊天上下文信息 (chat_stream)。"
            self.logger.error("RankCommand: execute 方法无法从 self 获取有效的 chat_stream。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天上下文错误消息也失败了: {send_e}")
            return False, "缺少聊天上下文 (chat_stream)", True

        stream_id = getattr(chat_stream, 'stream_id', None)
        if stream_id is None:
            error_msg = "❌ 无法获取聊天流ID (stream_id)。"
            self.logger.error("RankCommand: execute 方法无法从 chat_stream 获取有效的 stream_id。")
            try:
                await self.send_text(error_msg)
            except Exception as send_e:
                self.logger.error(f"发送聊天流ID错误消息也失败了: {send_e}")
            return False, "缺少聊天流ID (stream_id)", True

        # 3. 处理 'help' 子命令
        if rank_type == "help":
            help_text = (
                "📈 **避税与查询排行榜 帮助**\n\n"
                "🔹 **命令格式**:\n"
                "  `/rank` - 显示所有排行榜\n"
                "  `/rank tax` - 仅显示避税总量排行榜\n"
                "  `/rank freq` - 仅显示被查询次数排行榜\n"
                "  `/rank help` - 显示此帮助信息\n\n"
                "🔹 **说明**:\n"
                "  • 避税榜统计累计避税量 (ml)\n"
                "  • 查询榜统计被 `/ccb` 命令查询的次数"
            )
            try:
                await send_api.text_to_stream(
                    text=help_text,
                    stream_id=stream_id,
                )
                return True, "已发送排行榜帮助信息", True
            except Exception as e:
                error_msg = "❌ 发送帮助信息失败，请稍后重试。"
                self.logger.error(f"发送排行榜帮助时发生异常: {e}", exc_info=True)
                try:
                    await send_api.text_to_stream(
                        text=error_msg,
                        stream_id=stream_id
                    )
                except Exception as send_error:
                    self.logger.error(f"发送错误信息也失败了: {send_error}")
                return False, f"发送帮助信息失败: {e}", True

        # 4. 加载数据 (如果不是 help 命令)
        tax_data = _load_json_data("tax_totals.json")
        freq_data = _load_json_data("data.json")

        # 5. 确保加载的数据是字典
        tax_data = tax_data if isinstance(tax_data, dict) else {}
        freq_data = freq_data if isinstance(freq_data, dict) else {}

        # 6. 构造排行榜
        rank_lines = ["🏆 **群U避税与CB排行榜** 🏆"]
        has_data = False # 标记是否有任何数据被添加到排行榜

        if rank_type in ["all", "tax"]:
            rank_lines.append("\n🪙 **避税总量排行榜 (Top 10)**")
            if tax_data:
                # 过滤掉值为0或非数字的项，并按避税总量降序排序
                try:
                    filtered_tax = {k: v for k, v in tax_data.items() if isinstance(v, (int, float)) and v > 0}
                    if filtered_tax:
                        sorted_tax = sorted(filtered_tax.items(), key=lambda item: item[1], reverse=True)[:10]
                        for i, (qq, tax) in enumerate(sorted_tax, start=1):
                            rank_lines.append(f"  {i}. {qq} - {tax:.2f} ml")
                        has_data = True
                    else:
                        rank_lines.append("  暂无有效数据")
                except Exception as e:
                    self.logger.error(f"排序避税数据时出错: {e}")
                    rank_lines.append("  数据排序失败")
            else:
                rank_lines.append("  暂无数据")
            # 即使没有 tax_data，也标记为有内容（因为添加了标题）
            has_data = True

        if rank_type in ["all", "freq"]:
            rank_lines.append("\n👀 **被CB次数排行榜 (Top 10)**")
            if freq_data:
                # 过滤掉值为0或非整数的项，并按查询次数降序排序
                try:
                    filtered_freq = {k: v for k, v in freq_data.items() if isinstance(v, int) and v > 0}
                    if filtered_freq:
                        sorted_freq = sorted(filtered_freq.items(), key=lambda item: item[1], reverse=True)[:10]
                        for i, (qq, count) in enumerate(sorted_freq, start=1):
                            rank_lines.append(f"  {i}. {qq} - {count} 次")
                        has_data = True
                    else:
                        rank_lines.append("  暂无有效数据")
                except Exception as e:
                    self.logger.error(f"排序查询次数数据时出错: {e}")
                    rank_lines.append("  数据排序失败")
            else:
                rank_lines.append("  暂无数据")
            # 即使没有 freq_data，也标记为有内容（因为添加了标题）
            has_data = True

        # 如果没有任何数据（理论上不会发生，因为至少有标题），添加提示
        if not has_data: # 这个条件在当前逻辑下不太可能触发
            rank_lines.append("\n😔 暂时没有任何数据可以展示。快去 `/ccb` 几个QQ号试试吧！")

        message_text = "\n".join(rank_lines)

        # 7. 发送消息
        try:
            await send_api.text_to_stream(
                text=message_text,
                stream_id=stream_id,
            )
            return True, f"成功显示排行榜 (类型: {rank_type})", True
        except Exception as e:
            error_msg = "❌ 发送排行榜失败，请稍后重试。"
            self.logger.error(f"发送排行榜时发生异常: {e}", exc_info=True)
            try:
                await send_api.text_to_stream(
                    text=error_msg,
                    stream_id=stream_id
                )
            except Exception as send_error:
                self.logger.error(f"发送错误信息也失败了: {send_error}")
            return False, f"发送排行榜失败: {e}", True
