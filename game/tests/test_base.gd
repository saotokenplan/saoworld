extends Node

func assert(condition: bool, message: String = "Assertion failed") -> void:
	if not condition:
		print("ERROR: " + message)
		# In a real test framework, this would fail the test
		push_error(message)