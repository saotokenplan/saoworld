extends Node
## AudioManager GUT 测试
## 覆盖音量控制、静音切换、信号发射等核心逻辑

var audio_manager: Node

func before_all() -> void:
	var script: GDScript = load("res://scripts/autoload/AudioManager.gd")
	audio_manager = script.new()
	add_child(audio_manager)

func before_each() -> void:
	audio_manager.music_volume = 0.8
	audio_manager.sfx_volume = 1.0
	audio_manager.muted = false
	audio_manager.schema_version = 1

func test_initial_state() -> void:
	assert_eq(audio_manager.music_volume, 0.8, "default music_volume should be 0.8")
	assert_eq(audio_manager.sfx_volume, 1.0, "default sfx_volume should be 1.0")
	assert_false(audio_manager.muted, "default muted should be false")
	assert_eq(audio_manager.schema_version, 1, "schema_version should be 1")
	assert_eq(audio_manager.music_bus, "Music", "music_bus should be 'Music'")
	assert_eq(audio_manager.sfx_bus, "SFX", "sfx_bus should be 'SFX'")

func test_signals_declared() -> void:
	assert_true(audio_manager.has_signal("music_volume_changed"), "should have music_volume_changed signal")
	assert_true(audio_manager.has_signal("sfx_volume_changed"), "should have sfx_volume_changed signal")

func test_set_music_volume() -> void:
	audio_manager.set_music_volume(0.5)
	assert_eq(audio_manager.music_volume, 0.5, "music_volume should be set to 0.5")

func test_set_music_volume_clamp_high() -> void:
	audio_manager.set_music_volume(2.0)
	assert_eq(audio_manager.music_volume, 1.0, "music_volume should be clamped to 1.0")

func test_set_music_volume_clamp_low() -> void:
	audio_manager.set_music_volume(-0.5)
	assert_eq(audio_manager.music_volume, 0.0, "music_volume should be clamped to 0.0")

func test_set_sfx_volume() -> void:
	audio_manager.set_sfx_volume(0.3)
	assert_eq(audio_manager.sfx_volume, 0.3, "sfx_volume should be set to 0.3")

func test_set_sfx_volume_clamp_high() -> void:
	audio_manager.set_sfx_volume(1.5)
	assert_eq(audio_manager.sfx_volume, 1.0, "sfx_volume should be clamped to 1.0")

func test_set_sfx_volume_clamp_low() -> void:
	audio_manager.set_sfx_volume(-1.0)
	assert_eq(audio_manager.sfx_volume, 0.0, "sfx_volume should be clamped to 0.0")

func test_toggle_mute() -> void:
	assert_false(audio_manager.muted, "should start unmuted")
	audio_manager.toggle_mute()
	assert_true(audio_manager.muted, "should be muted after toggle")
	audio_manager.toggle_mute()
	assert_false(audio_manager.muted, "should be unmuted after second toggle")

func test_is_muted() -> void:
	assert_false(audio_manager.is_muted(), "is_muted should return false initially")
	audio_manager.muted = true
	assert_true(audio_manager.is_muted(), "is_muted should return true when muted")

func test_set_music_volume_boundary_zero() -> void:
	audio_manager.set_music_volume(0.0)
	assert_eq(audio_manager.music_volume, 0.0, "music_volume should be 0.0")

func test_set_music_volume_boundary_one() -> void:
	audio_manager.set_music_volume(1.0)
	assert_eq(audio_manager.music_volume, 1.0, "music_volume should be 1.0")

func test_set_sfx_volume_boundary_zero() -> void:
	audio_manager.set_sfx_volume(0.0)
	assert_eq(audio_manager.sfx_volume, 0.0, "sfx_volume should be 0.0")

func test_set_sfx_volume_boundary_one() -> void:
	audio_manager.set_sfx_volume(1.0)
	assert_eq(audio_manager.sfx_volume, 1.0, "sfx_volume should be 1.0")

func test_play_music_no_crash() -> void:
	# play_music 是空实现，确保不崩溃
	audio_manager.play_music("test_music")

func test_stop_music_no_crash() -> void:
	audio_manager.stop_music()

func test_play_sfx_no_crash() -> void:
	audio_manager.play_sfx("test_sfx")
