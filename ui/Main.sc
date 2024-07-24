[
	{ "keys": ["ctrl+shift+n"], "command": "new_window" },
	{ "keys": ["ctrl+shift+w"], "command": "close_window" },
	{ "keys": ["ctrl+o"], "command": "prompt_open_file" },
	{ "keys": ["ctrl+shift+t"], "command": "reopen_last_file" },
	{ "keys": ["alt+o"], "command": "switch_file", "args": {"extensions": ["cpp", "cxx", "cc", "c", "hpp", "hxx", "hh", "h", "ipp", "inl", "m", "mm"]} },
	{ "keys": ["ctrl+n"], "command": "new_file" },
	{ "keys": ["ctrl+s"], "command": "save" },
	{ "keys": ["ctrl+shift+s"], "command": "prompt_save_as" },
	{ "keys": ["ctrl+f4"], "command": "close_file" },
	{ "keys": ["ctrl+w"], "command": "close" },

	{ "keys": ["ctrl+k", "ctrl+b"], "command": "toggle_side_bar" },
	{ "keys": ["f11"], "command": "toggle_full_screen" },
	{ "keys": ["shift+f11"], "command": "toggle_distraction_free" },

	{ "keys": ["backspace"], "command": "left_delete" },
	{ "keys": ["shift+backspace"], "command": "left_delete" },
	{ "keys": ["ctrl+shift+backspace"], "command": "left_delete" },
	{ "keys": ["delete"], "command": "right_delete" },
	{ "keys": ["enter"], "command": "insert", "args": {"characters": "\n"} },
	{ "keys": ["shift+enter"], "command": "insert", "args": {"characters": "\n"} },

	{ "keys": ["ctrl+z"], "command": "undo" },
	{ "keys": ["ctrl+shift+z"], "command": "redo" },
	{ "keys": ["ctrl+y"], "command": "redo_or_repeat" },
	{ "keys": ["ctrl+u"], "command": "soft_undo" },
	{ "keys": ["ctrl+shift+u"], "command": "soft_redo" },

	{ "keys": ["shift+delete"], "command": "cut" },
	{ "keys": ["ctrl+insert"], "command": "copy" },
	{ "keys": ["shift+insert"], "command": "paste" },
	{ "keys": ["ctrl+x"], "command": "cut" },
	{ "keys": ["ctrl+c"], "command": "copy" },
	{ "keys": ["ctrl+v"], "command": "paste" },
	{ "keys": ["ctrl+shift+v"], "command": "paste_and_indent" },
	{ "keys": ["ctrl+k", "ctrl+v"], "command": "paste_from_history" },

	{ "keys": ["left"], "command": "move", "args": {"by": "characters", "forward": false} },
	{ "keys": ["right"], "command": "move", "args": {"by": "characters", "forward": true} },
	{ "keys": ["up"], "command": "move", "args": {"by": "lines", "forward": false} },
	{ "keys": ["down"], "command": "move", "args": {"by": "lines", "forward": true} },
	{ "keys": ["shift+left"], "command": "move", "args": {"by": "characters", "forward": false, "extend": true} },
	{ "keys": ["shift+right"], "command": "move", "args": {"by": "characters", "forward": true, "extend": true} },
	{ "keys": ["shift+up"], "command": "move", "args": {"by": "lines", "forward": false, "extend": true} },
	{ "keys": ["shift+down"], "command": "move", "args": {"by": "lines", "forward": true, "extend": true} },

	{ "keys": ["ctrl+left"], "command": "move", "args": {"by": "words", "forward": false} },
	{ "keys": ["ctrl+right"], "command": "move", "args": {"by": "word_ends", "forward": true} },
	{ "keys": ["ctrl+shift+left"], "command": "move", "args": {"by": "words", "forward": false, "extend": true} },
	{ "keys": ["ctrl+shift+right"], "command": "move", "args": {"by": "word_ends", "forward": true, "extend": true} },

	{ "keys": ["alt+left"], "command": "move", "args": {"by": "subwords", "forward": false} },
	{ "keys": ["alt+right"], "command": "move", "args": {"by": "subword_ends", "forward": true} },
	{ "keys": ["alt+shift+left"], "command": "move", "args": {"by": "subwords", "forward": false, "extend": true} },
	{ "keys": ["alt+shift+right"], "command": "move", "args": {"by": "subword_ends", "forward": true, "extend": true} },

	{ "keys": ["ctrl+alt+up"], "command": "select_lines", "args": {"forward": false} },
	{ "keys": ["ctrl+alt+down"], "command": "select_lines", "args": {"forward": true} },

	{ "keys": ["pageup"], "command": "move", "args": {"by": "pages", "forward": false} },
	{ "keys": ["pagedown"], "command": "move", "args": {"by": "pages", "forward": true} },
	{ "keys": ["shift+pageup"], "command": "move", "args": {"by": "pages", "forward": false, "extend": true} },
	{ "keys": ["shift+pagedown"], "command": "move", "args": {"by": "pages", "forward": true, "extend": true} },

	{ "keys": ["home"], "command": "move_to", "args": {"to": "bol", "extend": false} },
	{ "keys": ["end"], "command": "move_to", "args": {"to": "eol", "extend": false} },
	{ "keys": ["shift+home"], "command": "move_to", "args": {"to": "bol", "extend": true} },
	{ "keys": ["shift+end"], "command": "move_to", "args": {"to": "eol", "extend": true} },
	{ "keys": ["ctrl+home"], "command": "move_to", "args": {"to": "bof", "extend": false} },
	{ "keys": ["ctrl+end"], "command": "move_to", "args": {"to": "eof", "extend": false} },
	{ "keys": ["ctrl+shift+home"], "command": "move_to", "args": {"to": "bof", "extend": true} },
	{ "keys": ["ctrl+shift+end"], "command": "move_to", "args": {"to": "eof", "extend": true} },


	{ "keys": ["ctrl+up"], "command": "scroll_lines", "args": {"amount": 1.0 } },
	{ "keys": ["ctrl+down"], "command": "scroll_lines", "args": {"amount": -1.0 } },

	{ "keys": ["ctrl+pagedown"], "command": "next_view" },
	{ "keys": ["ctrl+pageup"], "command": "prev_view" },

	{ "keys": ["ctrl+tab"], "command": "next_view_in_stack" },
	{ "keys": ["ctrl+shift+tab"], "command": "prev_view_in_stack" },

	{ "keys": ["ctrl+a"], "command": "select_all" },
	{ "keys": ["ctrl+shift+l"], "command": "split_selection_into_lines" },
	{ "keys": ["escape"], "command": "single_selection", "context":
		[
			{ "key": "num_selections", "operator": "not_equal", "operand": 1 }
		]
	},
	{ "keys": ["escape"], "command": "clear_fields", "context":
		[
			{ "key": "has_next_field", "operator": "equal", "operand": true }
		]
	}
]
