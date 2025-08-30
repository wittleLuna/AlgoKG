#!/usr/bin/env python3
"""
测试实体提取功能
"""
import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

from app.services.note_entity_extractor import NoteEntityExtractor

async def test_extraction():
    """测试实体提取"""
    print("开始测试实体提取...")

    try:
        extractor = NoteEntityExtractor()
        print("实体提取器创建成功")

        test_content = """
        ### 括号序列

        > 唐僧师徒途经一座神秘的古庙，庙前刻着一行字："欲往决赛，需解此阵！" 小码哥自告奋勇上前查看，发现地上刻着一串由"("和")"括号组成的符号（长度为偶数），显然是某种法阵，但次序混乱，使得灵气无法流转。
        > 小码哥看了一眼，笑道："这法阵应该是要变成一套匹配的符号，才能显现出通往西天的正确道路，但怎么判断是否匹配呢？"
        > 悟空指着庙旁的一块石碑说道："规则在这儿！

        这是一个典型的括号匹配问题，可以使用栈来解决。
        """

        print("开始提取实体...")
        result = await extractor.extract_entities_from_note("test_note", test_content, "括号匹配")
        print("实体提取完成")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"提取结果:")
    print(f"实体数量: {len(result.entities)}")
    print(f"关系数量: {len(result.relations)}")
    print(f"元数据: {result.extraction_metadata}")
    
    print("\n实体列表:")
    for entity in result.entities:
        print(f"- {entity.name} ({entity.type}) - 置信度: {entity.confidence}")
    
    print("\n关系列表:")
    for relation in result.relations:
        print(f"- {relation.source_entity} -> {relation.target_entity} ({relation.relation_type})")

if __name__ == "__main__":
    asyncio.run(test_extraction())
