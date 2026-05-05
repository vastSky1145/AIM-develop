import os
import re
import time
import json
from typing import Iterable

from langchain_core.documents import Document
from openai import OpenAI

from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter, TextSplitter

text2 = """"
10月23日，中国共产党第二十届中央委员会第四次全体会议公报发布。根据公报，全会高度评价“十四五”时期我国发展取得的重大成就，并提出了“十五五”时期经济社会发展的主要目标。相比于“十四五”时期，当前我国的发展环境有何不同？下一个五年，我国经济社会发展的主要目标是什么？未来五年，我国高质量发展的落脚点是什么？科技自立自强水平大幅提高的抓手有哪些？

　　每经记者|张宏  石雨昕    每经编辑|张益铭    

　　“十四五”收官，“十五五”启航。

　　中国共产党第二十届中央委员会第四次全体会议（以下简称“全会”），于2025年10月20日至23日在北京举行。

　　10月23日，中国共产党第二十届中央委员会第四次全体会议公报（以下简称“公报”）发布。根据公报，全会高度评价“十四五”时期我国发展取得的重大成就，并提出了“十五五”时期经济社会发展的主要目标。

　　相比于“十四五”时期，当前我国的发展环境有何不同？下一个五年，我国经济社会发展的主要目标是什么？未来五年，我国高质量发展的落脚点是什么？科技自立自强水平大幅提高的抓手有哪些？作为推动经济增长的“三驾马车”，下一阶段，消费、投资、进出口如何发力？

　　针对这些问题，《每日经济新闻》记者展开研究、采访。

　　更加强化对风险挑战的重视程度

　　相比于“十四五”时期，当前我国的发展环境有何不同？

　　2020年，站在“十四五”起点，中国共产党第十九届中央委员会第五次全体会议深入分析了我国发展环境面临的深刻复杂变化，认为当前（2020年）和今后一个时期，我国发展仍然处于重要战略机遇期，但机遇和挑战都有新的发展变化。

　　站在“十五五”起点，全会指出，“十五五”时期我国发展环境面临深刻复杂变化，我国发展处于战略机遇和风险挑战并存、不确定难预料因素增多的时期。我国经济基础稳、优势多、韧性强、潜能大，长期向好的支撑条件和基本趋势没有变，中国特色社会主义制度优势、超大规模市场优势、完整产业体系优势、丰富人才资源优势更加彰显。

　　中泰证券研究所政策组首席分析师杨畅在接受《每日经济新闻》记者（以下简称每经记者）微信采访时表示，公报前半部分的表述转变意味着我国对“十五五”的发展阶段形成了更加深刻的判断，尤其是并未保留“战略机遇期”的相关提法，相应表述调整为“战略机遇和风险挑战并存”，需要在“十五五”发展期间，更加强化对风险挑战的重视程度，更加强化对“不确定难预料因素增多”的预判，需要做好积极应对和提前准备。

　　杨畅进一步指出，“我国经济基础稳、优势多、韧性强、潜能大，长期向好的支撑条件和基本趋势没有变，中国特色社会主义制度优势、超大规模市场优势、完整产业体系优势、丰富人才资源优势更加彰显”相关表述，也更加强调了，在“十五五”时期，我国内部具有非常充分的积极因素，完全有能力应对各种风险挑战。

　　对科技给予了更加明确的定位

　　全会提出“十五五”时期经济社会发展的主要目标：高质量发展取得显著成效，科技自立自强水平大幅提高，进一步全面深化改革取得新突破，社会文明程度明显提升，人民生活品质不断提高，美丽中国建设取得新的重大进展，国家安全屏障更加巩固。在此基础上再奋斗五年，到二〇三五年实现我国经济实力、科技实力、国防实力、综合国力和国际影响力大幅跃升，人均国内生产总值达到中等发达国家水平，人民生活更加幸福美好，基本实现社会主义现代化。

　　针对科技发展，全会提出，加快高水平科技自立自强，引领发展新质生产力。抓住新一轮科技革命和产业变革历史机遇，统筹教育强国、科技强国、人才强国建设，提升国家创新体系整体效能，全面增强自主创新能力，抢占科技发展制高点，不断催生新质生产力。

　　东方金诚首席宏观分析师王青接受每经记者文字采访时表示，我国经济发展必须转向创新驱动，转向以高技术制造业和服务业为代表的新动能。这也意味着，尽管当前房地产等旧动能调整带来一定经济下行压力，但培育壮大新质生产力，坚持创新驱动，推动新旧动能转换的发展战略不会动摇。

　　杨畅表示，全会对于科技给予了更加明确的定位，后续按照“十五五”规划的要求，有望进一步保持甚至加大对科技领域的支持力度。

　　科技自立自强水平大幅提高的抓手有哪些？

　　中国建投投资研究院主任、研究员张志前在接受每经记者微信采访时表示，实现科技自立自强，对于实现经济高质量发展和完成“十五五”规划目标任务具有非常重要的意义。实现科技自立自强水平大幅提高，首先要抓住新一轮科技革命和产业变革历史机遇，加强科技原始创新和关键核心技术的攻关，彻底摆脱关键核心技术受制于人的局面。其次，要深化科技体制改革，优化新型举国体制、原创技术激发机制。坚持企业科技创新的主体地位，深化产学研深度合作，发挥科技领军企业作用，构建创新生态系统。最后，要统筹教育强国、科技强国、人才强国建设，提升国家创新体系整体效能，全面增强自主创新能力。

　　未来五年，我国高质量发展的落脚点是什么？

　　张志前认为，推动我国经济高质量发展是全面建设社会主义现代化国家的必然要求，也是破解发展不平衡不充分问题、实现可持续发展的选择。推动我国经济高质量发展取得成效，首先，要加快发展新质生产力，建设现代化产业体系。坚持智能化绿色化发展方向，用现代科学技术改造传统产业，实现传统产业的转型升级。其次，要继续扩大内需，构建国内统一大市场，促进投资和消费、供给和需求良性互动，加快构建新发展格局。最后，继续深化改革，完善体制机制，把有为政府和有效市场有机结合，激发各类经营主体活力，确保高质量发展行稳致远。

　　“三驾马车”如何发力？

　　作为推动经济增长的“三驾马车”，下一阶段，消费、投资、进出口如何发力？

　　全会提出，坚持扩大内需这个战略基点，坚持惠民生和促消费、投资于物和投资于人紧密结合，以新需求引领新供给，以新供给创造新需求，促进消费和投资、供给和需求良性互动，增强国内大循环内生动力和可靠性。

　　五年前，中国共产党第十九届中央委员会第五次全体会议提出“以创新驱动、高质量供给引领和创造新需求”，而本次强调了“以新需求引领新供给，以新供给创造新需求”，如何理解这一表述上的转变？

　　中国消费经济学会副理事长洪涛接受每经记者电话采访时表示，全会强调新需求引领新供给，有利于使供给更加有针对性地满足实际需求，减少和避免无效投资，推动高质量发展。

　　如何理解“投资于物和投资于人紧密结合”？

　　洪涛指出，除了过去经常提到的“投资于物”，全会还强调“投资于人”，体现了人民至上的原则，这意味着未来将更加重视城乡居民直接消费和公共消费，这两方面的发展不仅需要政府的投资支持，也需要吸引民间资本等多方面的经济成分共同参与投资。

　　针对改善民生，全会提出，加大保障和改善民生力度，扎实推进全体人民共同富裕。坚持尽力而为、量力而行，加强普惠性、基础性、兜底性民生建设，解决好人民群众急难愁盼问题，畅通社会流动渠道，提高人民生活品质。要促进高质量充分就业，完善收入分配制度，办好人民满意的教育，健全社会保障体系，推动房地产高质量发展，加快建设健康中国，促进人口高质量发展，稳步推进基本公共服务均等化。

　　上海易居房地产研究院副院长严跃进接受每经记者微信采访时表示，房地产业发展，一定要立足于民生导向，精细化推进系列工作。一方面，解决住房问题，本身就是民生改善的重要体现。尤其是要围绕“房价稳定”这一民生关注最多的内容，持续做好房价方面的管理工作，真正让买卖双方预期稳定、交易顺畅。另一方面，要全面围绕补短板推进系列工作。包括城中村改造、老旧小区改造、危旧房改造、原拆原建工作、加装电梯和更换电梯，以及“一老一小”等系列工作，都是加大保障和改善民生力度的重要体现。

　　针对对外开放，全会提出，扩大高水平对外开放，开创合作共赢新局面。稳步扩大制度型开放，维护多边贸易体制，拓展国际循环，以开放促改革促发展，与世界各国共享机遇、共同发展。要积极扩大自主开放，推动贸易创新发展，拓展双向投资合作空间，高质量共建“一带一路”。


　　东方金诚研究发展部执行总监冯琳接受《每日经济新闻》记者文字采访时表示，这一表述意味着增强国内大循环，强化内需驱动绝非“关起门来搞建设”，未来我国将更好利用国际国内两个市场、两种资源，通过国内和国际市场有效联通，改善经济增长中的全要素生产率。下一步，一方面是依托我国大市场优势，通过扩大商品进口，培育国内消费市场，带动国内制造业转型升级；另一方面是进一步加大服务业开放，全面增强服务业竞争力，打造“中国服务”品牌。“中国制造”在开放竞争中崛起，未来推动“中国服务”，增强国际竞争力，开放竞争仍是必由之路。

　　杨畅认为，根据“与世界各国共享机遇、共同发展”相关表述来看，有望进一步加大国内相关服务领域的开放力度，吸引全球加大对我国投资力度；根据“拓展双向投资合作空间”相关表述，有望推动我国企业出海的步伐，为企业开展全球性布局提供支撑。
"""

#文本预处理，根据“##”分块

# text2 = text2.split("##")

text_splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
recursive_text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
recursive_result = []

# ========== 基本配置 ==========
MY_API_KEY = os.getenv("MY_API_KEY", "sk-sZi4nNPwuQhqBNonGrHL0yATSQKHOi88AJiiGFQfdG5xoD1l")  # 这里修改为你获取的API-KEY
API_BASE_URL = os.getenv("MY_API_BASE", "https://api.chat.csu.edu.cn/v1")

# 初始化 OpenAI 客户端
client = OpenAI(api_key=MY_API_KEY, base_url=API_BASE_URL)


# 初始化使用模型
MODEL_NAME = os.getenv("MY_MODEL", "DeepSeek-V4-Flash")
def split_chunks_assisted_by_thinking_model(text: str) -> tuple[str,str]:
    """
    向模型提问并返回思考内容和答案。
    :param text:
    :return: tuple[str,str]
        - 思考内容
        - 答案
    """
    messages = [
        # {"role": "system", "content": ""},
        {"role": "system", "content": """你是一个有问必答的AI助手。你的任务是对输入的文本，根据语义进行分块，每块大小在150字到350字之间，并按json格式返回格式，格式示例如下
        {
            "chunks" : [
                "文本1",
                "文本2",
                "文本3"
            ]
        }
        """},
        {"role": "user", "content": text}
    ]

    try:
        # 调用模型 API
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1024 * 128,
            temperature=0.7,
            stream=False,
            # 如果你使用deepseek-v4模型，我们部署的当前版本是V4 flash，可以通过以下开关开启思考模式。
            # 具体参考https://github.com/sgl-project/sglang/tree/main/benchmark/deepseek_v3
            # 开启思考模式后，需要取思考内容，需从resp.choices[0].message.reasoning_content
            extra_body={"chat_template_kwargs": {"thinking": True}}
        )

        # 从响应中提取答案文本
        if resp and resp.choices and resp.choices[0].message:
            # return resp.choices[0].message.content.strip()
            # 获取思考内容
            return (resp.choices[0].message.reasoning_content.strip(),
                    resp.choices[0].message.content.strip())
        else:
            return None, "模型没有返回有效的答案。"

    except Exception as e:
        return None, f"调用模型时发生错误: {e}"

# def split_documents_assisted_by_thinking_model(documents: Iterable[Document]) -> list[Document]:
#     """Split documents."""
#     result_docs = []
#     for doc in documents:
#         chunks = self._split_text(doc.page_content)
#         for chunk in chunks:
#             new_doc = Document(page_content=chunk, metadata=doc.metadata)
#             result_docs.append(new_doc)
#     return result_docs


class ThinkingModelTextSplitter(TextSplitter):
    def __init__(self, model_client, model_name: str = "DeepSeek-V4-Flash", chunk_min: int = 150, chunk_max: int = 350, **kwargs):
        super().__init__(**kwargs)
        self.client = model_client
        self.model_name = model_name
        self.chunk_min = chunk_min
        self.chunk_max = chunk_max

    def split_text(self, text: str) -> list[str]:
        thinking, result = split_chunks_assisted_by_thinking_model(text)
        try:
            data = json.loads(result)
            chunks = data.get("chunks", [])
            if not chunks:
                print("⚠️ 模型未返回有效的 chunks，返回原文。")
                return [text]
            return chunks
        except Exception as e:
            print(f"⚠️ JSON 解析失败: {e}")
            return [text]

    def split_documents(self, documents: Iterable[Document]) -> list[Document]:
        """兼容 LangChain 的 split_documents() 方法"""
        result_docs = []
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                result_docs.append(new_doc)
        return result_docs



if __name__ == "__main__":
    
    thinking_content, answer = split_chunks_assisted_by_thinking_model(text2)
    print("-------------以下是思考内容-------------")
    print(thinking_content)
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("-------------以下是答案-------------")
    print(answer)


    # 将JSON字符串转换为Python对象
    data = json.loads(answer)

    # 现在data是一个字典，包含chunks列表
    print(type(data))  # <class 'dict'>
    print(len(data["chunks"]))  # 11个文本块

    # 您可以访问各个chunk
    for i, chunk in enumerate(data["chunks"]):
        print(f"Chunk {i + 1}: {chunk[:50]}...")  # 打印每个chunk的前50个字符