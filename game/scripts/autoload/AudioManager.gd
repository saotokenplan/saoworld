extends Node
## 音频管理器
## 负责管理背景音乐、音效、音频配置

signal music_volume_changed(volume: float)
signal sfx_volume_changed(volume: float)

var music_bus: String = "Music"
var sfx_bus: String = "SFX"
var music_volume: float = 0.8
var sfx_volume: float = 1.0
var muted: bool = false
var schema_version: int = 1

func _ready() -> void:
	_load_config()
	_apply_volume()

func set_music_volume(volume: float) -> void:
	music_volume = clamp(volume, 0.0, 1.0)
	_apply_volume()
	_save_config()
	music_volume_changed.emit(music_volume)

func set_sfx_volume(volume: float) -> void:
	sfx_volume = clamp(volume, 0.0, 1.0)
	_apply_volume()
	_save_config()
	sfx_volume_changed.emit(sfx_volume)

func toggle_mute() -> void:
	muted = not muted
	_apply_volume()
	_save_config()

func is_muted() -> bool:
	return muted

func play_music(music_name: String) -> void:
	pass

func stop_music() -> void:
	pass

func play_sfx(sfx_name: String) -> void:
	pass

func _apply_volume() -> void:
	var music_vol: float = music_volume if not muted else 0.0
	var sfx_vol: float = sfx_volume if not muted else 0.0
	
	if AudioServer.bus_exists(music_bus):
		var bus_idx: int = AudioServer.get_bus_index(music_bus)
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(music_vol))
	
	if AudioServer.bus_exists(sfx_bus):
		var bus_idx: int = AudioServer.get_bus_index(sfx_bus)
		AudioServer.set_bus_volume_db(bus_idx, linear_to_db(sfx_vol))

func _save_config() -> void:
	var save_data: Dictionary = {
		"schema_version": schema_version,
		"music_volume": music_volume,
		"sfx_volume": sfx_volume,
		"muted": muted
	}
	var file := FileAccess.open("user://audio_config.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data))
		file.close()

func _load_config() -> void:
	if not FileAccess.file_exists("user://audio_config.json"):
		return
	var file := FileAccess.open("user://audio_config.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		file.close()
		var parsed: Variant = JSON.parse_string(content)
		if typeof(parsed) == TYPE_DICTIONARY:
			var data: Dictionary = parsed
			if data.has("schema_version"):
				schema_version = data["schema_version"]
			if data.has("music_volume"):
				music_volume = data["music_volume"]
			if data.has("sfx_volume"):
				sfx_volume = data["sfx_volume"]
			if data.has("muted"):
				muted = data["muted"]
