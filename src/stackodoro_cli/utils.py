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

def merge_layers_with_color(
    text_canvas: list[str], 
    attr_canvas: list[list[str | None]], 
    foreground: list[str], 
    start_y: int, 
    color_attr: str | None
):
    required_height = start_y + len(foreground)
    if required_height > len(text_canvas):
        extension = [""] * (required_height - len(text_canvas))
        text_canvas.extend(extension)
        for _ in range(required_height - len(attr_canvas)):
            attr_canvas.append([])

    for i, fg_row in enumerate(foreground):
        current_y = start_y + i
        if current_y < 0: continue
            
        bg_row = text_canvas[current_y]
        
        stripped_fg = fg_row.strip()
        if not stripped_fg:
            max_len = max(len(bg_row), len(fg_row))
            text_canvas[current_y] = bg_row.ljust(max_len)
            _pad_attr_row(attr_canvas, current_y, max_len)
            continue

        start_index = fg_row.find(stripped_fg[0])
        end_index = fg_row.rfind(stripped_fg[-1])
        max_len = max(len(bg_row), len(fg_row))
        
        text_canvas[current_y] = merge_row(bg_row, fg_row)

        _pad_attr_row(attr_canvas, current_y, max_len)
        row_attrs = attr_canvas[current_y]
        
        for x in range(start_index, end_index + 1):
            row_attrs[x] = color_attr

def _pad_attr_row(attr_canvas, row_idx, length):
    while len(attr_canvas) <= row_idx:
        attr_canvas.append([])
    row = attr_canvas[row_idx]
    if len(row) < length:
        row.extend([None] * (length - len(row)))

def render_urwid_markup(text_canvas: list[str], attr_canvas: list[list[str | None]]):
    markup = []
    
    for y, line in enumerate(text_canvas):
        if y >= len(attr_canvas):
            markup.append(line)
            markup.append('\n')
            continue
            
        row_attrs = attr_canvas[y]
        current_attr = None
        current_text = []
        
        for x, char in enumerate(line):
            attr = row_attrs[x] if x < len(row_attrs) else None
            
            if attr != current_attr:
                if current_text:
                    markup.append((current_attr if current_attr else '', "".join(current_text)))
                current_attr = attr
                current_text = []
            
            current_text.append(char)
        
        if current_text:
             markup.append((current_attr or '', "".join(current_text)))
        
        markup.append('\n')
        
    return markup

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
