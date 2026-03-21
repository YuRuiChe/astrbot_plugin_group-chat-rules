from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core import AstrBotConfig

# @register 装饰器用于注册插件，参数依次为：插件名、作者、描述、版本、仓库地址
@register("astrbot_plugin_group-chat-rules", "语芮澈", "可以判断群规是否适合当前场景", "v5", "https://github.com/YuRuiChe/astrbot_plugin_group-chat-rules")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 这里可以初始化插件的配置或资源
        # 不要在配置文件里写默认值！！！！！！在这里写默认值！！！！！！（因为这里都是集中到一起的，好找）
        self.llm_provide = config.get("llm_provide", "")
        self.is_regulations = config.get("is_regulations", "1、践行社会主义价值观2、坚决不违反法律、道德与纪律")
        self.open_review = config.get("content_review", {}).get("open_review", False)
        self.withdraw_the_illegal_content = config.get("content_review", {}).get("withdraw_the_illegal_content", False)
        self.send_warning_message = config.get("content_review", {}).get("send_warning_message", False)
        self.warning_message = config.get("content_review", {}).get("warning_message", "你的发言违反了群规！")

        if self.llm_provide:
            logger.info(f"插件使用提供商: {self.llm_provide}")
        else:
            logger.info("未选择提供商，请用户在配置中选择")



    # @filter.command 装饰器定义一个指令
    @filter.command("群规判断")
    async def query_regulations (self, event: AstrMessageEvent, prompt: str):
        '''判断此言论是否符合群规'''  # 这里的注释会被解析为指令描述，建议填写
        user_name = event.get_sender_name() # 获取发送者的名字
        logger.info(f"用户 {user_name} 发送了群规请求") # 使用AstrBot的日志接口
        try:
            # 获取配置文件选择的LLM提供商ID
            provider_id = self.llm_provide
            if not provider_id:
                yield event.plain_result("❌无法获取 LLM 提供商，请先在 WebUI 中配置 LLM")
                return
            logger.info(f"使用提供商: {provider_id}, 用户问题: {prompt}")
            # 调用 LLM 生成回答
            llm_response = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=prompt,
                system_prompt= f"群规如下“{self.is_regulations}” 判断此言论“{prompt}”是否符合群规，如果违反，请输出“你的发言含有违规内容，违反了第XXX条（要有此条的具体内容）”；如果没有违反，那就输出“没有违反群规”。用简洁的中文回答，不要有多余的输出。"
            )
            # 获取回复内容
            reply = llm_response.completion_text
            # 发送回复
            yield event.plain_result(f"AI生成，仅做参考\n\n{reply}")
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            yield event.plain_result(f"❌ 调用 LLM 时出错: {str(e)}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent, prompt):
        """群规判断"""
        # 检查是否启用
        if self.config.get("open_review", False):
            return
        # 排除机器人自己的消息
        if event.is_from_self():
            return
        # 根据消息类型决定是否回复
        is_private = event.is_private_chat()
        is_group = not is_private
        if is_private and not self.config.get("reply_private", True):
            return
        if is_group and not self.config.get("reply_group", True):
            return
        # 获取消息内容
        message = event.message_str
        # 获取发送者的名字
        user_name = event.get_sender_name()
        try:
            # 获取配置文件选择的LLM提供商ID
            provider_id = self.llm_provide
            if not provider_id:
                yield event.plain_result("❌无法获取 LLM 提供商，请先在 WebUI 中配置 LLM")
                return
            logger.info(f"使用提供商: {provider_id}, 用户问题: {prompt}")
            # 调用 LLM 生成回答
            llm_response = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=prompt,
                system_prompt=f"群规如下“{self.is_regulations}” 判断此言论“{prompt}”是否符合群规，如果违反，请输出“Y”这个字母；如果没有违反，那就输出“N”这个字母，坚决不要有多余的输出。"
            )
            # 获取回复内容
            reply = llm_response.completion_text
            # 发送回复
            if self.config.get("open_review", True):
                if reply == "Y":
                    if is_group:
                        # 群聊：@用户
                        yield event.chain_result([
                            Comp.At(qq=event.get_sender_id()),
                            Comp.Plain(f"{self.warning_message}")
                        ])
                    else:
                        # 私聊：直接回复
                        yield event.plain_result(reply)
                else:
                    return
            else:
                return
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            yield event.plain_result(f"❌ 调用 LLM 时出错: {str(e)}")

    async def terminate(self):
        '''当插件被卸载或停用时调用，用于释放资源（如关闭数据库连接、停止定时任务等）'''
        logger.info("插件正在终止...")
        # 在这里添加你的清理代码
        pass