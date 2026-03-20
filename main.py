from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core import AstrBotConfig

# @register 装饰器用于注册插件，参数依次为：插件名、作者、描述、版本、仓库地址
@register("astrbot_plugin_group-chat-rules", "语芮澈", "可以判断群规是否适合当前场景", "v1.0", "https://github.com/YuRuiChe/astrbot_plugin_group-chat-rules")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 这里可以初始化插件的配置或资源
        self.is_regulations = config.get("is_regulations", "我是群规")


    # @filter.command 装饰器定义一个指令
    @filter.command("群规判断")
    async def query_regulations (self, event: AstrMessageEvent, prompt: str):
        '''判断此言论是否符合群规'''  # 这里的注释会被解析为指令描述，建议填写
        user_name = event.get_sender_name() # 获取发送者的名字
        logger.info(f"用户 {user_name} 发送了群规请求") # 使用 AstrBot 的日志接口
        try:
            # 1. 获取当前会话的唯一标识
            umo = event.unified_msg_origin
            # 2. 获取当前会话使用的 LLM 提供商 ID
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
            if not provider_id:
                yield event.plain_result("❌ 无法获取 LLM 提供商，请先在 WebUI 中配置 LLM")
                return
            logger.info(f"使用提供商: {provider_id}, 用户问题: {prompt}")
            # 3. 调用 LLM 生成回答
            llm_response = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=prompt,
                system_prompt= f"群规如下“{self.is_regulations}” 判断此言论“{prompt}”是否符合群规，如果违反，请输出“你的发言含有违规内容，违反了第XXX条（要有此条的具体内容）”；如果没有违反，那就输出“没有违反群规”。用简洁的中文回答，不要有多余的输出。"
            )
            # 4. 获取回复内容
            reply = llm_response.completion_text
            # 5. 发送回复
            yield event.plain_result(f"AI生成，仅做参考\n\n{reply}")
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            yield event.plain_result(f"❌ 调用 LLM 时出错: {str(e)}")

    async def terminate(self):
        '''当插件被卸载或停用时调用，用于释放资源（如关闭数据库连接、停止定时任务等）'''
        logger.info("插件正在终止...")
        # 在这里添加你的清理代码
        pass