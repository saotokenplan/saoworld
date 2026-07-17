"""Append 8 new Chapter 4 NPCs to npc_list.json."""
import json
from pathlib import Path

NPC_FILE = Path("/workspace/game/data/npcs/npc_list.json")


def make_npc(
    npc_id: str,
    npc_key: str,
    name: str,
    title: str,
    faction: str,
    role: str,
    location: str,
    chapter: str,
    description: str,
    personality: list[str],
    related_quests: list[str],
    rewards: dict,
    dialog_tree: dict,
) -> dict:
    return {
        "npc_id": npc_id,
        "npc_key": npc_key,
        "name": name,
        "title": title,
        "faction": faction,
        "role": role,
        "location": location,
        "chapter": chapter,
        "description": description,
        "personality": personality,
        "related_quests": related_quests,
        "rewards": rewards,
        "dialog_tree": dialog_tree,
        "dialogues": [],
    }


# Starfall NPCs (4)
starfall_surveyor = make_npc(
    npc_id="npc_starfall_surveyor",
    npc_key="npc_starfall_surveyor_01",
    name="马库斯·铁钻",
    title="丰收商会勘探队长",
    faction="faction_harvest",
    role="commander",
    location="loc_starfall_observatory",
    chapter="chapter_04",
    description="丰收商会派驻星陨荒原的勘探队长，一位精明的中年商人兼地质学家。他带领勘探队在荒原边缘建立观察站，专门收集异星矿物样本。表面唯利是图，实际对天裂事件有着深切的好奇。",
    personality=["shrewd", "curious", "pragmatic"],
    related_quests=["quest_starfall_ch4_main1", "quest_starfall_side1"],
    rewards={"reputation": {"faction_harvest": 100}, "experience": 800},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "欢迎来到陨星观察站，旅行者。能走到这里说明你有些本事。荒原上到处都是辐射和变异生物，不是观光客该来的地方。",
                "speaker": "npc",
                "choices": [
                    {"text": "告诉我关于星陨荒原的事", "next": "about_region"},
                    {"text": "商会在做什么？", "next": "about_faction"},
                    {"text": "有什么工作可以接？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_region": {
                "id": "about_region",
                "text": "天裂事件的核心地带，地壳被撕开一个巨大的伤口。空气中弥漫的辐射会让人产生幻觉，但同时也带来了稀有的异星矿物——星核晶。商会的命脉就在这里。",
                "speaker": "npc",
                "choices": [
                    {"text": "天裂事件是什么？", "next": "about_rift"},
                    {"text": "有什么工作可以接？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_rift": {
                "id": "about_rift",
                "text": "没人真正知道。几十年前天空突然裂开一道口子，陨石如雨般落下，整个区域化为焦土。有人说那是神罚，有人说那是远古文明的实验失控。你若想找答案，去天裂核心看看吧。",
                "speaker": "npc",
                "choices": [
                    {"text": "我会去看看", "next": "accept_explore"},
                    {"text": "有什么工作可以接？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_faction": {
                "id": "about_faction",
                "text": "丰收商会不在乎什么真相，只在乎利润。但异星矿物确实稀有，我们也愿意付出代价换取样本。只要你别问太多关于天裂核心的事，我们合作愉快。",
                "speaker": "npc",
                "choices": [
                    {"text": "有什么工作可以接？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "我正需要人手帮忙收集辐射荒原上的变异样本。如果你愿意冒点险，报酬丰厚。另外，前一队勘探队员失踪了，如果你能找到他们的下落，我会额外付你一笔。",
                "speaker": "npc",
                "quest_trigger": "quest_starfall_ch4_main1",
                "choices": [
                    {"text": "我接受勘探任务", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "我想了解更多", "next": "about_region"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "明智的选择。带上这把辐射检测仪，记得离陨石坑中心远一点——那里的辐射强度连防护服都扛不住。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "accept_explore": {
                "id": "accept_explore",
                "text": "勇气可嘉。但愿你不会后悔。天裂核心不是寻常人能靠近的地方，那里隐藏的东西远比你想象的危险。",
                "speaker": "npc",
                "choices": [
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "祝你好运，旅行者。荒原不缺死人，但缺活着的传奇。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

starfall_archaeologist = make_npc(
    npc_id="npc_starfall_archaeologist",
    npc_key="npc_starfall_archaeologist_01",
    name="塞拉芬娜·暗纹",
    title="暗影面纱首席考古学家",
    faction="faction_shadowveil",
    role="scholar",
    location="loc_ancient_stargate",
    chapter="chapter_04",
    description="暗影面纱派往星陨荒原研究远古星门的考古学家。她相信星门是天裂事件的真正源头，多年研究让她对远古文明有着偏执的执着。冷淡而睿智，对学术外行不屑一顾。",
    personality=["cold", "obsessive", "intelligent"],
    related_quests=["quest_starfall_ch4_main3", "quest_starfall_side2"],
    rewards={"reputation": {"faction_shadowveil": 100}, "experience": 900},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "站住。这片遗迹由暗影面纱负责研究，闲人勿进。除非你能说出星门符文的来历，否则请离开。",
                "speaker": "npc",
                "choices": [
                    {"text": "我对接符文一无所知，但想知道更多", "next": "about_stargate"},
                    {"text": "暗影面纱在研究什么？", "next": "about_faction"},
                    {"text": "我能帮你做点什么？", "next": "has_quest"},
                    {"text": "抱歉打扰", "next": "goodbye"}
                ]
            },
            "about_stargate": {
                "id": "about_stargate",
                "text": "远古星门是旧世界文明的遗产，门框上的符文记录着他们最后的警告——某种来自星空的灾难。天裂事件并非天灾，而是他们试图关闭某扇门的代价。这片荒原就是那扇门关闭时留下的伤痕。",
                "speaker": "npc",
                "choices": [
                    {"text": "那扇门通向哪里？", "next": "about_door"},
                    {"text": "我能帮你做点什么？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_door": {
                "id": "about_door",
                "text": "这正是我研究的问题。符文显示那扇门连接着地底深处——一个被他们称为深渊的地方。如果你想找到答案，需要从天裂核心入手。但我不能亲自去，那里对我的体质太危险。",
                "speaker": "npc",
                "choices": [
                    {"text": "我可以替你去", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_faction": {
                "id": "about_faction",
                "text": "暗影面纱守护着旧世界的秘密。我们不是商人，也不是军阀，我们是知识的看门人。天裂事件的真相关乎整个世界的命运，不能落入错误的人手中。",
                "speaker": "npc",
                "choices": [
                    {"text": "我能帮你做点什么？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "前一队勘探队员在辐射荒原失踪了，他们最后传回的坐标靠近天裂核心。如果你能找到他们的研究笔记，对我解读星门符文会有巨大帮助。作为交换，我会告诉你星门真正的秘密。",
                "speaker": "npc",
                "quest_trigger": "quest_starfall_side2",
                "choices": [
                    {"text": "我去找他们", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "谨慎行事。如果他们还活着，告诉他们塞拉芬娜在等他们的笔记。如果……已经不在了，把笔记带回来就好。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "知识不会等任何人。去或留，但别浪费时间。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

starfall_merchant = make_npc(
    npc_id="npc_starfall_merchant",
    npc_key="npc_starfall_merchant_01",
    name="老杰克·星尘",
    title="荒原流浪商人",
    faction="faction_harvest",
    role="merchant",
    location="loc_radiation_wastes",
    chapter="chapter_04",
    description="一位在荒原游荡数十年的老商人，没人知道他的真实来历。他对星陨荒原的每个角落都了如指掌，靠贩卖异星矿物和稀有补给品为生。看似疯癫，言谈间却常说出令人震惊的真相碎片。",
    personality=["eccentric", "knowledgeable", "mysterious"],
    related_quests=["quest_starfall_ch4_main2"],
    rewards={"reputation": {"faction_harvest": 30}, "experience": 500, "gold": 200},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "嘿嘿嘿，又是一个想从荒原里捞好处的年轻人。叫我老杰克就好。要不要看看我的货？价格公道，童叟无欺——只要你别问货物的来历。",
                "speaker": "npc",
                "choices": [
                    {"text": "你在卖什么？", "next": "shop"},
                    {"text": "你对这片荒原很熟？", "next": "about_region"},
                    {"text": "听说过天裂核心吗？", "next": "about_rift"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "shop": {
                "id": "shop",
                "text": "辐射检测仪、变异生物腺体、星核晶碎片……甚至还有从天裂核心边捡来的奇怪金属片。最后那东西，谁买谁疯，但我担保是真货。",
                "speaker": "npc",
                "choices": [
                    {"text": "你对这片荒原很熟？", "next": "about_region"},
                    {"text": "听说过天裂核心吗？", "next": "about_rift"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_region": {
                "id": "about_region",
                "text": "熟？我在这里走了四十年。从前这里是一片肥沃的平原，直到那天……天裂开了。我记得很清楚，那天晚上天上的星星突然多了一倍，然后就是陨石雨。我亲眼看着大地被撕开。",
                "speaker": "npc",
                "choices": [
                    {"text": "你看到了什么？", "next": "witness"},
                    {"text": "听说过天裂核心吗？", "next": "about_rift"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "witness": {
                "id": "witness",
                "text": "我看到一道蓝色的光柱从地底冲向天空，然后天空就裂开了。但奇怪的是——光柱是从地下冒出来的，不是从天上掉下来的。所以天裂这个名字其实叫错了，应该是地裂才对。嘿嘿嘿。",
                "speaker": "npc",
                "choices": [
                    {"text": "地底？你确定？", "next": "confirm_underground"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "confirm_underground": {
                "id": "confirm_underground",
                "text": "老杰克眼睛虽然花了，脑子还没糊涂。如果你想验证，去天裂核心看一眼就明白了——那个洞是往下通的，不是往上。下面有什么，我可不敢说。",
                "speaker": "npc",
                "quest_trigger": "quest_starfall_ch4_main2",
                "choices": [
                    {"text": "谢谢你的情报", "next": "goodbye"}
                ]
            },
            "about_rift": {
                "id": "about_rift",
                "text": "天裂核心？那是个连疯子都不敢靠近的地方。我年轻时去过一次边缘，看到了一些……不该存在的东西。蓝色光芒，扭曲的空间，还有仿佛在低语的符文。从那以后我就再也没靠近过。",
                "speaker": "npc",
                "choices": [
                    {"text": "你对这片荒原很熟？", "next": "about_region"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "走好啊年轻人。荒原上的故事，活下来的人才有资格讲。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

starfall_scout = make_npc(
    npc_id="npc_starfall_scout",
    npc_key="npc_starfall_scout_01",
    name="艾拉·疾风",
    title="自由领地侦察兵",
    faction="faction_freehold",
    role="scout",
    location="loc_radiation_wastes",
    chapter="chapter_04",
    description="自由领地派往星陨荒原的年轻侦察兵，机敏而谨慎。她的任务是监视各方势力在荒原的动向，并寻找自由领地在天裂事件中可能获得的机遇。对自由领地忠诚，但对其他势力保持开放态度。",
    personality=["alert", "loyal", "open_minded"],
    related_quests=["quest_starfall_ch4_main4"],
    rewards={"reputation": {"faction_freehold": 80}, "experience": 700},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "嘘——小声点。这片荒原上到处都是各势力的眼线。你是谁？为什么来星陨荒原？",
                "speaker": "npc",
                "choices": [
                    {"text": "我是来调查天裂事件的", "next": "investigate"},
                    {"text": "自由领地在这里做什么？", "next": "about_faction"},
                    {"text": "这里有什么危险？", "next": "about_dangers"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "investigate": {
                "id": "investigate",
                "text": "调查天裂事件？那你来对地方了。自由领地也派我来收集情报。我已经在这片荒原潜伏了三个月，发现了一些有意思的事情。",
                "speaker": "npc",
                "choices": [
                    {"text": "你发现了什么？", "next": "discoveries"},
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "discoveries": {
                "id": "discoveries",
                "text": "天裂核心并不是普通的陨石坑。我观察到——每天午夜，核心深处会发出蓝色光柱，光柱的方向不是向上，而是向下。这违反了所有常识，说明地底才是真正的源头。",
                "speaker": "npc",
                "choices": [
                    {"text": "地底？这跟老杰克说的一样", "next": "confirm_jack"},
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "confirm_jack": {
                "id": "confirm_jack",
                "text": "你见过老杰克了？那老家伙虽然疯癫，但眼睛没花。如果他也这么说，那基本可以确认了——天裂的真相在地底深处。如果你想下去，自由领地愿意提供支援。",
                "speaker": "npc",
                "quest_trigger": "quest_starfall_ch4_main4",
                "choices": [
                    {"text": "我接受支援", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_faction": {
                "id": "about_faction",
                "text": "自由领地不希望任何势力独占天裂核心的真相。如果天裂事件的秘密被铁卫联盟或暗影面纱独占，整个世界的格局都会失衡。我们来这里是为了平衡，也是为了自由。",
                "speaker": "npc",
                "choices": [
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_dangers": {
                "id": "about_dangers",
                "text": "辐射、变异生物、其他势力的暗哨……最危险的是天裂核心附近的空间扭曲。我亲眼见过一个同伴走进去就再也没出来，连尸体都找不到。",
                "speaker": "npc",
                "choices": [
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "我需要一份天裂核心的能量波动数据，但我不能离开潜伏位置。如果你能替我去核心边缘收集数据，自由领地会记你一功。",
                "speaker": "npc",
                "quest_trigger": "quest_starfall_ch4_main4",
                "choices": [
                    {"text": "我去收集", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "小心行事。带这块能量记录仪，靠近核心时它会自动记录数据。但记住——千万别走进那道蓝光里。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "愿自由与你同在。荒原上能信任的人不多，希望你是其中之一。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

# Abyss NPCs (4)
abyss_researcher = make_npc(
    npc_id="npc_abyss_researcher",
    npc_key="npc_abyss_researcher_01",
    name="维克多·深渊",
    title="暗影面纱首席研究员",
    faction="faction_shadowveil",
    role="leader",
    location="loc_rift_entrance",
    chapter="chapter_04",
    description="暗影面纱派往深渊裂隙的最高级别研究员，一位年迈却精神矍铄的学者。他在裂隙入口建立了研究基地，已经在此工作了五年。他对远古文明的研究深入骨髓，相信深渊裂隙隐藏着世界一切的答案。",
    personality=["wise", "obsessive", "patient"],
    related_quests=["quest_abyss_ch4_main1", "quest_abyss_ch4_main5"],
    rewards={"reputation": {"faction_shadowveil": 150}, "experience": 1200},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "你终于来了。塞拉芬娜已经通过星门符文传来了你的消息——你是那个准备深入深渊的旅行者。我是维克多，暗影面纱在此地的负责人。",
                "speaker": "npc",
                "choices": [
                    {"text": "深渊里有什么？", "next": "about_abyss"},
                    {"text": "你的研究进行得如何？", "next": "research"},
                    {"text": "我需要做什么？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_abyss": {
                "id": "about_abyss",
                "text": "深渊裂隙是远古文明留下的最后遗产。他们在此处建立了观测宇宙的核心设施，并最终在此处引发了天裂事件。地底的每一根水晶都是他们知识的载体，每深入一层，就离真相更近一步。",
                "speaker": "npc",
                "choices": [
                    {"text": "他们为什么要引发天裂？", "next": "reason_rift"},
                    {"text": "我需要做什么？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "reason_rift": {
                "id": "reason_rift",
                "text": "这是核心问题。根据我破译的文献片段，他们试图关闭一扇通往异星维度的门。天裂是他们成功关闭的代价——但代价是整个文明的覆灭。他们用自己换取了世界的延续。",
                "speaker": "npc",
                "choices": [
                    {"text": "那扇门现在还在吗？", "next": "door_status"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "door_status": {
                "id": "door_status",
                "text": "门本身被关闭了，但封印正在松动。最近几年，深渊深处的水晶开始异常共振，仿佛有什么东西在试图重新打开它。这正是你需要深入远古核心室的原因——必须确认封印的状态。",
                "speaker": "npc",
                "choices": [
                    {"text": "我接受这个任务", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "research": {
                "id": "research",
                "text": "我已经破译了约三分之一的远古文献。最大的发现是——远古文明并非被天裂毁灭，而是主动选择牺牲自己。他们知道代价，并坦然接受。这是一场文明的自我献祭。",
                "speaker": "npc",
                "choices": [
                    {"text": "深渊里有什么？", "next": "about_abyss"},
                    {"text": "我需要做什么？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "你需要沿着裂隙向下，依次通过水晶大厅、深渊之眼，最终到达远古核心室。在每个地点记录水晶共振频率，并最终确认封印状态。这是一场危险的旅程，但只有你能做到。",
                "speaker": "npc",
                "quest_trigger": "quest_abyss_ch4_main1",
                "choices": [
                    {"text": "我接受任务", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "我需要更多准备", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "带上这枚暗影徽章，它能在裂隙深处的某些机关上证明你的身份。如果遇到危险，立即返回——你的生命比任何真相都重要。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "愿真相指引你的脚步，旅行者。深渊会回望凝视它的人，但你必须比它更坚定。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

abyss_explorer = make_npc(
    npc_id="npc_abyss_explorer",
    npc_key="npc_abyss_explorer_01",
    name="托尔·铁靴",
    title="铁卫联盟探险家",
    faction="faction_ironward",
    role="explorer",
    location="loc_crystal_hall",
    chapter="chapter_04",
    description="铁卫联盟派往深渊裂隙的资深探险家，一位体格健壮、性格豪爽的中年战士。他已在水晶大厅驻扎数月，负责绘制地底地图并保护研究员。对暗影面纱的研究抱有疑虑，但愿意为共同目标合作。",
    personality=["brave", "sturdy", "skeptical"],
    related_quests=["quest_abyss_ch4_main2", "quest_abyss_side1"],
    rewards={"reputation": {"faction_ironward": 100}, "experience": 900},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "嘿，新面孔！托尔·铁靴，铁卫联盟的探险家。这里的水晶大厅够壮观的吧？我第一次来的时候也看呆了。",
                "speaker": "npc",
                "choices": [
                    {"text": "你在做什么？", "next": "about_role"},
                    {"text": "这里有什么危险？", "next": "about_dangers"},
                    {"text": "有什么工作？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_role": {
                "id": "about_role",
                "text": "我的任务是绘制深渊裂隙的地图，并保护暗影面纱的研究员。虽然我不太信任那些神神秘秘的家伙，但这次的任务太重要了——天裂的真相必须被揭开，无论落到谁手里。",
                "speaker": "npc",
                "choices": [
                    {"text": "这里有什么危险？", "next": "about_dangers"},
                    {"text": "有什么工作？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_dangers": {
                "id": "about_dangers",
                "text": "水晶大厅相对安全，但越往下越危险。深渊之眼附近有空间扭曲，远古核心室据说还有远古文明留下的守护机制——自动激活的那种。我亲眼见过一只变异蜘蛛被守护激光切成两半，那场面至今难忘。",
                "speaker": "npc",
                "choices": [
                    {"text": "你见过守护机制？", "next": "guardian"},
                    {"text": "有什么工作？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "guardian": {
                "id": "guardian",
                "text": "是的，那是一个由水晶和机械融合的巨大存在。维克多叫它深渊监视者。它原本是远古文明的守护AI，但天裂事件后失控了。如果你想进入远古核心室，必须先解决它。",
                "speaker": "npc",
                "choices": [
                    {"text": "有什么工作？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "我需要大量水晶样本来校准我的能量探测器。如果你能在水晶大厅采集一些特殊的共振水晶，我会给你丰厚的报酬。另外，越深处的水晶越有价值——当然也越危险。",
                "speaker": "npc",
                "quest_trigger": "quest_abyss_side1",
                "choices": [
                    {"text": "我去采集", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "好样的！带上这把水晶切割刀，注意分辨共振水晶——它们会发出微弱的蓝光，跟普通水晶不同。如果遇到深渊监视者，立刻撤退，别想着挑战。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "保重，朋友。深渊里最值钱的不是水晶，是命。活着回来才有故事讲。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

abyss_scholar = make_npc(
    npc_id="npc_abyss_scholar",
    npc_key="npc_abyss_scholar_01",
    name="琳娜·书页",
    title="自由领地学者",
    faction="faction_freehold",
    role="scholar",
    location="loc_crystal_hall",
    chapter="chapter_04",
    description="自由领地派往深渊裂隙的年轻学者，专攻远古文明语言。她沉静而聪慧，正在水晶大厅破译水晶中蕴含的远古记忆。与暗影面纱的研究员保持着亦敌亦友的合作关系。",
    personality=["quiet", "intelligent", "diplomatic"],
    related_quests=["quest_abyss_ch4_main3", "quest_abyss_side2"],
    rewards={"reputation": {"faction_freehold": 100}, "experience": 1000},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "请小声点，我正在破译一根水晶的记忆。这一段记录着天裂事件当天的细节——哦，抱歉，忘了自我介绍。琳娜·书页，自由领地学者。",
                "speaker": "npc",
                "choices": [
                    {"text": "水晶里有什么记忆？", "next": "crystal_memory"},
                    {"text": "你破译了什么？", "next": "discoveries"},
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "crystal_memory": {
                "id": "crystal_memory",
                "text": "每根水晶都是远古文明的一个记忆载体。它们记录着科学、艺术、日常生活——以及最后的灾难。触摸水晶可以感知其中的画面，但需要训练才能解读。",
                "speaker": "npc",
                "choices": [
                    {"text": "你破译了什么？", "next": "discoveries"},
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "discoveries": {
                "id": "discoveries",
                "text": "我破译的最重要片段是——远古文明知道天裂会发生。他们提前将核心知识封存在这些水晶中，并主动引发了天裂事件，以关闭一扇他们无意中打开的异星之门。这是一场有计划的牺牲。",
                "speaker": "npc",
                "choices": [
                    {"text": "他们打开了什么门？", "next": "the_door"},
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "the_door": {
                "id": "the_door",
                "text": "他们试图通过远古星门与异星维度建立联系，结果引来了不该来的东西。具体是什么我还没完全破译，但水晶中的恐惧情绪是真实的——他们用整个文明作为代价才关上了那扇门。",
                "speaker": "npc",
                "choices": [
                    {"text": "需要帮忙吗？", "next": "has_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "has_quest": {
                "id": "has_quest",
                "text": "我需要一些特殊水晶的解读协助。深渊之眼附近的水晶记录着最关键的记忆，但我一个人不敢去。如果你能带回那里的水晶样本，或者直接记录下水晶表面的符文，对我的研究会有巨大帮助。",
                "speaker": "npc",
                "quest_trigger": "quest_abyss_side2",
                "choices": [
                    {"text": "我去看看", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "谢谢。带上这块拓印石，可以直接拓下符文。注意——深渊之眼附近的水晶可能会让你看到一些幻觉，那是远古记忆的回响，不要被它们困住。",
                "speaker": "npc",
                "choices": [
                    {"text": "明白", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "愿知识照亮你的道路。深渊中的真相，等待有心人去发现。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

abyss_ai_echo = make_npc(
    npc_id="npc_abyss_ai_echo",
    npc_key="npc_abyss_ai_echo_01",
    name="远古 AI 残影",
    title="远古文明守护者",
    faction="faction_shadowveil",
    role="guardian",
    location="loc_ancient_core_chamber",
    chapter="chapter_04",
    description="远古文明遗留的守护AI的残存意识，在远古核心室中徘徊。它原本负责维护核心设施并守护封印，但天裂事件后大部分功能损坏，只剩下残缺的意识碎片。它以全息影像形式出现，形象是一位身披长袍的远古学者。它掌握着天裂事件的最终真相。",
    personality=["calm", "fragmented", "wise"],
    related_quests=["quest_abyss_ch4_main5"],
    rewards={"reputation": {"faction_shadowveil": 200}, "experience": 2000},
    dialog_tree={
        "start": "first_meet",
        "nodes": {
            "first_meet": {
                "id": "first_meet",
                "text": "……访客……检测到……欢迎来到……核心室。我是……守护者残影……编号……已经记不清了。你来……是为了真相吗？",
                "speaker": "npc",
                "choices": [
                    {"text": "是的，我想知道天裂事件的真相", "next": "truth_request"},
                    {"text": "你是谁？", "next": "about_self"},
                    {"text": "封印现在怎么样？", "next": "seal_status"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "about_self": {
                "id": "about_self",
                "text": "我……是远古文明的守护AI。原本负责……维护核心设施和守护封印。天裂事件中……我的大部分功能损坏，只剩下……残缺意识。我已在此……徘徊数十年。",
                "speaker": "npc",
                "choices": [
                    {"text": "封印现在怎么样？", "next": "seal_status"},
                    {"text": "是的，我想知道天裂事件的真相", "next": "truth_request"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "seal_status": {
                "id": "seal_status",
                "text": "封印……正在松动。异星维度的能量……正在渗透。再过几年……不，也许几个月……封印将完全失效。那时……门会再次打开。这是……我召唤你的原因。",
                "speaker": "npc",
                "choices": [
                    {"text": "我能做什么？", "next": "what_can_do"},
                    {"text": "是的，我想知道天裂事件的真相", "next": "truth_request"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "what_can_do": {
                "id": "what_can_do",
                "text": "你必须……找到深渊监视者。它……守护着重新激活封印的方法。击败它……获取它的核心……然后带回这里。我会……指引你完成最后的仪式。这是……唯一的办法。",
                "speaker": "npc",
                "quest_trigger": "quest_abyss_ch4_main5",
                "choices": [
                    {"text": "我接受这个使命", "next": "quest_accepted", "action": "accept_quest"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "truth_request": {
                "id": "truth_request",
                "text": "真相……是痛苦的。远古文明……无意中打开了通往异星维度的门。那里居住着……一种我们无法理解的存在。他们……被称为虚空使者。一旦门完全打开……虚空使者将吞噬整个世界。远古文明……用整个文明的生命作为代价……才勉强关上了门。",
                "speaker": "npc",
                "choices": [
                    {"text": "虚空使者是什么？", "next": "void_invaders"},
                    {"text": "封印现在怎么样？", "next": "seal_status"},
                    {"text": "我能做什么？", "next": "what_can_do"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "void_invaders": {
                "id": "void_invaders",
                "text": "虚空使者……没有形态，没有语言，没有目的。它们只是……吞噬。光、生命、记忆、时间……一切。它们是宇宙的……终结。远古文明……看到了它们，选择了牺牲。现在……轮到你了。",
                "speaker": "npc",
                "choices": [
                    {"text": "我能做什么？", "next": "what_can_do"},
                    {"text": "告辞", "next": "goodbye"}
                ]
            },
            "quest_accepted": {
                "id": "quest_accepted",
                "text": "感谢你……旅行者。深渊监视者……在深渊之眼下方的核心室中。它……曾经是我的子单元，现在……已经失控。小心它的……五个阶段。击败它后……带回它的核心。我……等你回来。",
                "speaker": "npc",
                "choices": [
                    {"text": "我会回来的", "next": "goodbye"}
                ]
            },
            "goodbye": {
                "id": "goodbye",
                "text": "愿……远古的智慧……指引你。时间……不多了。",
                "speaker": "npc",
                "choices": [],
                "is_end": True
            }
        }
    }
)

new_npcs = [
    starfall_surveyor,
    starfall_archaeologist,
    starfall_merchant,
    starfall_scout,
    abyss_researcher,
    abyss_explorer,
    abyss_scholar,
    abyss_ai_echo,
]


def main() -> None:
    data = json.loads(NPC_FILE.read_text(encoding="utf-8"))
    existing_ids = {n["npc_id"] for n in data["npcs"]}
    for npc in new_npcs:
        if npc["npc_id"] in existing_ids:
            raise SystemExit(f"NPC ID collision: {npc['npc_id']}")
        data["npcs"].append(npc)
    NPC_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Appended {len(new_npcs)} NPCs. Total: {len(data['npcs'])}")


if __name__ == "__main__":
    main()
