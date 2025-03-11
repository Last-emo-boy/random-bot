import random
import time
import asyncio
import logging
from web3 import Web3
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

# 设置日志记录器
logger = logging.getLogger("RandomPlugin")
logger.setLevel(logging.DEBUG)

@register("random", "w33d", "基于区块数生成随机数", "1.3.0", "https://github.com/Last-emo-boy/random-bot/")
class RandomPlugin(Star):
    # 请替换为你实际的以太坊RPC节点地址，如 Infura 的地址
    ETH_NODE_URL = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.w3 = Web3(Web3.HTTPProvider(self.ETH_NODE_URL))
        logger.info("RandomPlugin 初始化完成")
    
    async def get_block(self, block_identifier):
        """异步获取区块信息"""
        try:
            block = await asyncio.to_thread(self.w3.eth.get_block, block_identifier)
            logger.debug(f"成功获取区块 {block_identifier}，区块号: {block.number}")
            return block
        except Exception as e:
            logger.error(f"获取区块 {block_identifier} 失败: {e}")
            return None

    @filter.command("random", alias=["抽签"])
    async def random(self, event: AstrMessageEvent, min_val: int = None, max_val: int = None, count: int = 1):
        '''基于最新三个区块生成随机数或抽签结果。
        
        参数:
          min_val (int, 可选): 随机数范围的最小值。
          max_val (int, 可选): 随机数范围的最大值。
          count (int, 可选): 抽取数量（默认1）。
          
        使用示例：
          /random                   -> 返回三个区块信息及生成的随机种子
          /random 1 100             -> 在 [1, 100] 范围内生成一个随机数
          /random 1 100 3           -> 在 [1, 100] 范围内随机抽取3个不重复数字
          
        输出中将显示最终的结果及随机性的来源（所用区块的区块号和区块哈希）。'''
        
        # 返回初步提示
        yield event.plain_result("收到请求，正在处理，请稍候...")
        logger.info(f"收到随机请求，参数: min_val={min_val}, max_val={max_val}, count={count}")
        
        # 获取最新三个区块：最新、最新-1、最新-2
        latest_block = await self.get_block("latest")
        if not latest_block:
            yield event.plain_result("错误：无法获取最新区块信息，请检查节点连接。")
            return
        
        latest_number = latest_block.number
        block1 = latest_block
        block2 = await self.get_block(latest_number - 1)
        block3 = await self.get_block(latest_number - 2)
        if not block2 or not block3:
            yield event.plain_result("错误：无法获取足够的区块信息，请检查节点连接。")
            return
        
        # 获取三个区块的哈希
        hash1 = block1.hash.hex()
        hash2 = block2.hash.hex()
        hash3 = block3.hash.hex()
        
        # 组合三个哈希生成随机种子
        seed_str = hash1 + hash2 + hash3
        seed = int(seed_str, 16)
        logger.debug(f"生成随机种子: {seed}，来源哈希: {hash1}, {hash2}, {hash3}")
        
        # 使用种子初始化随机数生成器
        random.seed(seed)
        
        # 如果未提供随机范围，则仅返回区块信息和随机种子
        if min_val is None or max_val is None:
            message = (
                f"随机性来源：\n"
                f"区块1: #{block1.number} - {hash1}\n"
                f"区块2: #{block2.number} - {hash2}\n"
                f"区块3: #{block3.number} - {hash3}\n"
                f"生成的随机种子: {seed}"
            )
            logger.info("仅返回区块信息和随机种子")
            yield event.plain_result(message)
        else:
            if min_val > max_val:
                logger.error("参数错误：min_val 大于 max_val")
                yield event.plain_result("错误：最小值不能大于最大值。")
                return
            
            range_size = max_val - min_val + 1
            if count > range_size:
                logger.error("参数错误：抽取数量超过范围内可选值数量")
                yield event.plain_result("错误：抽取数量超过范围内的可选值数量。")
                return
            
            # 生成不重复的随机结果
            numbers = list(range(min_val, max_val + 1))
            random.shuffle(numbers)
            results = numbers[:count]
            logger.info(f"生成随机结果: {results}")
            
            message = (
                f"随机抽签结果:\n"
                f"范围: [{min_val}, {max_val}]\n"
                f"抽取数量: {count}\n"
                f"结果: {results}\n\n"
                f"随机性来源：\n"
                f"区块1: #{block1.number} - {hash1}\n"
                f"区块2: #{block2.number} - {hash2}\n"
                f"区块3: #{block3.number} - {hash3}\n"
                f"生成的随机种子: {seed}"
            )
            yield event.plain_result(message)
    
    async def terminate(self):
        '''插件卸载时调用'''
        logger.info("RandomPlugin 被卸载")
        pass
