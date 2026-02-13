import shutil

def merge_row(bg_row: str, fg_row: str) -> str:
    # identify solid bounds of the foreground
    stripped_fg = fg_row.strip()
    if not stripped_fg:
        return bg_row

    start_index = fg_row.find(stripped_fg[0])
    end_index = fg_row.rfind(stripped_fg[-1])

    max_len = max(len(bg_row), len(fg_row))
    bg_row = bg_row.ljust(max_len)
    fg_row = fg_row.ljust(max_len)

    result = []
    for i in range(max_len):
        # if inside the solid part of the foreground, use foreground
        if start_index <= i <= end_index:
            result.append(fg_row[i])
        else:
            result.append(bg_row[i])

    return "".join(result)

def merge_layers(background: list[str], foreground: list[str], start_y: int) -> list[str]:
    canvas = background[:]
    
    required_height = start_y + len(foreground)
    if required_height > len(canvas):
        extension = [""] * (required_height - len(canvas))
        canvas.extend(extension)

    for i, fg_line in enumerate(foreground):
        current_y = start_y + i        
        if current_y < 0: 
            continue
            
        bg_line = canvas[current_y]
        canvas[current_y] = merge_row(bg_line, fg_line)

    return canvas

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def center_canvas_on_screen(canvas_lines):
    term_cols, term_rows = shutil.get_terminal_size()
    
    canvas_height = len(canvas_lines)
    canvas_width = max(len(line) for line in canvas_lines) if canvas_lines else 0
    
    pad_top = max(0, (term_rows - canvas_height) // 2)
    pad_left = max(0, (term_cols - canvas_width) // 2)
    
    final_output = [""] * pad_top
    
    padding_str = " " * pad_left
    for line in canvas_lines:
        final_output.append(padding_str + line)
    
    pad_bottom = max(0, term_rows - len(final_output))
    final_output.extend([""] * pad_bottom)
        
    return final_output
