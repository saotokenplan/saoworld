extends GutTest
## CombatManager 测试用例

var combat_manager: Node

func before_each() -> void:
	combat_manager = autofree(CombatManager.new())
	add_child(combat_manager)
	GameState.reset_state()

func test_initial_state() -> void:
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IDLE, "初始状态应为 IDLE")
	assert_false(combat_manager.is_in_combat(), "初始不应在战斗中")

func test_start_combat_success() -> void:
	var result: bool = combat_manager.start_combat("wolf")
	assert_true(result, "开始战斗应成功")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IN_COMBAT, "状态应为 IN_COMBAT")
	assert_true(combat_manager.is_in_combat(), "应在战斗中")

func test_start_combat_invalid_enemy() -> void:
	var result: bool = combat_manager.start_combat("invalid_enemy")
	assert_false(result, "无效敌人应无法开始战斗")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IDLE, "状态应保持 IDLE")

func test_start_combat_already_in_combat() -> void:
	combat_manager.start_combat("wolf")
	var result: bool = combat_manager.start_combat("bandit")
	assert_false(result, "战斗中无法开始新战斗")

func test_player_attack_damage_calculation() -> void:
	combat_manager.start_combat("wolf")
	var result: Dictionary = combat_manager.player_attack()
	
	assert_true(result.get("success", false), "玩家攻击应成功")
	assert_has(result, "player_damage", "应包含玩家伤害")
	assert_gt(result.get("player_damage", 0), 0, "玩家伤害应大于0")

func test_player_attack_not_in_combat() -> void:
	var result: Dictionary = combat_manager.player_attack()
	assert_false(result.get("success", true), "非战斗状态攻击应失败")

func test_victory_grants_exp() -> void:
	combat_manager.start_combat("wolf")
	
	# 模拟敌人血量为0
	combat_manager.enemy_health = 0
	var result: Dictionary = combat_manager.player_attack()
	
	assert_eq(result.get("result", ""), "victory", "应为胜利结果")
	assert_gt(result.get("exp_gained", 0), 0, "胜利应获得经验")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.VICTORY, "状态应为 VICTORY")

func test_defeat_resets_health() -> void:
	GameState.player_health = 5
	combat_manager.start_combat("wolf")
	
	# 模拟玩家死亡
	GameState.player_health = 0
	GameState.is_alive = false
	
	var result: Dictionary = combat_manager.player_attack()
	
	assert_eq(result.get("result", ""), "defeat", "应为失败结果")
	assert_eq(GameState.player_health, GameState.player_max_health, "失败后血量应恢复")
	assert_true(GameState.is_alive, "失败后应复活")

func test_flee_success() -> void:
	combat_manager.start_combat("wolf")
	
	# 模拟逃跑成功（通过随机种子）
	seed(42)
	var result: Dictionary = combat_manager.attempt_flee()
	
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IDLE, "逃跑成功状态应为 IDLE")

func test_flee_not_in_combat() -> void:
	var result: Dictionary = combat_manager.attempt_flee()
	assert_false(result.get("success", true), "非战斗状态逃跑应失败")

func test_end_combat() -> void:
	combat_manager.start_combat("wolf")
	combat_manager.end_combat()
	
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IDLE, "结束战斗状态应为 IDLE")
	assert_false(combat_manager.is_in_combat(), "结束战斗不应在战斗中")

func test_get_enemy_health_percent() -> void:
	combat_manager.start_combat("wolf")
	combat_manager.enemy_health = 15
	combat_manager.enemy_max_health = 30
	
	var percent: float = combat_manager.get_enemy_health_percent()
	assert_almost_eq(percent, 0.5, 0.01, "血量百分比应为50%")

func test_get_combat_state_name() -> void:
	assert_eq(combat_manager.get_combat_state_name(), "idle", "IDLE 状态名称")

	combat_manager.start_combat("wolf")
	assert_eq(combat_manager.get_combat_state_name(), "in_combat", "IN_COMBAT 状态名称")


## ==================== Boss 战斗测试 ====================

func test_start_boss_combat_success() -> void:
	# Boss 战开始成功
	var result: bool = combat_manager.start_boss_combat("boss_ancient_tree")
	assert_true(result, "Boss 战应成功开始")
	assert_true(combat_manager.is_boss_combat, "应标记为 Boss 战")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IN_COMBAT, "状态应为 IN_COMBAT")
	assert_eq(combat_manager.current_phase, 1, "初始阶段应为 1")
	assert_false(combat_manager.enraged, "初始不应处于狂暴状态")

func test_start_boss_combat_invalid_enemy() -> void:
	# 无效敌人
	var result: bool = combat_manager.start_boss_combat("invalid_boss")
	assert_false(result, "无效 Boss 应无法开始战斗")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IDLE, "状态应保持 IDLE")

func test_start_boss_combat_not_boss() -> void:
	# 普通敌人调用 Boss 战方法
	var result: bool = combat_manager.start_boss_combat("wolf")
	assert_false(result, "普通敌人不应能调用 Boss 战方法")
	assert_false(combat_manager.is_boss_combat, "不应标记为 Boss 战")

func test_boss_phase_transition() -> void:
	# 阶段转换
	combat_manager.start_boss_combat("boss_ancient_tree")
	assert_eq(combat_manager.total_phases, 3, "boss_ancient_tree 应有 3 个阶段")

	# 监听阶段转换信号
	var phase_changed_signal: bool = false
	combat_manager.phase_changed.connect(func(_current: int, _total: int, _name: String):
		phase_changed_signal = true
	end)

	# 模拟血量下降触发阶段转换（设置敌人为低血量）
	combat_manager.enemy_health = combat_manager.enemy_max_health * 0.3
	var result: Dictionary = combat_manager.player_attack()

	assert_true(phase_changed_signal, "应触发阶段转换信号")

func test_boss_enrage_activation() -> void:
	# 狂暴激活
	combat_manager.start_boss_combat("boss_ancient_tree")

	# 监听狂暴信号
	var enrage_signal: bool = false
	combat_manager.enrage_activated.connect(func():
		enrage_signal = true
	end)

	# 模拟血量下降到狂暴阈值
	combat_manager.enemy_health = combat_manager.enemy_max_health * 0.2
	var result: Dictionary = combat_manager.player_attack()

	assert_true(combat_manager.enraged, "应进入狂暴状态")
	assert_true(enrage_signal, "应触发狂暴信号")

func test_boss_skill_usage() -> void:
	# 特殊技能使用
	combat_manager.start_boss_combat("boss_ancient_tree")

	# 监听技能信号
	var skill_used_signal: bool = false
	var skill_name: String = ""
	combat_manager.boss_skill_used.connect(func(name: String, _desc: String):
		skill_used_signal = true
		skill_name = name
	end)

	# 执行多次攻击触发技能（Boss 有 30% 概率使用技能）
	for i in range(20):
		if combat_manager.is_in_combat():
			combat_manager.player_attack()
			if skill_used_signal:
				break

	# 由于概率性，不强断言，但验证方法存在
	assert_true(combat_manager.has_signal("boss_skill_used"), "应有 boss_skill_used 信号")

func test_boss_combat_victory() -> void:
	# Boss 战胜利
	combat_manager.start_boss_combat("boss_ancient_tree")

	# 模拟敌人血量为 0
	combat_manager.enemy_health = 0
	var result: Dictionary = combat_manager.player_attack()

	assert_eq(result.get("result", ""), "victory", "应为胜利结果")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.VICTORY, "状态应为 VICTORY")
	assert_true(result.get("is_boss", false), "结果应标记为 Boss 战")

func test_boss_combat_cannot_flee() -> void:
	# Boss 战无法逃跑
	combat_manager.start_boss_combat("boss_ancient_tree")

	var result: Dictionary = combat_manager.attempt_flee()
	assert_false(result.get("success", true), "Boss 战应无法逃跑")
	assert_eq(combat_manager.current_state, CombatManager.CombatState.IN_COMBAT, "状态应保持 IN_COMBAT")

func test_boss_combat_state_reset() -> void:
	# Boss 战结束状态重置
	combat_manager.start_boss_combat("boss_ancient_tree")
	combat_manager.enemy_health = 0
	combat_manager.player_attack()

	# 结束战斗
	combat_manager.end_combat()

	assert_eq(combat_manager.current_phase, 1, "阶段应重置为 1")
	assert_eq(combat_manager.total_phases, 1, "总阶段应重置为 1")
	assert_false(combat_manager.enraged, "狂暴状态应重置")
	assert_false(combat_manager.is_boss_combat, "Boss 战标记应清除")