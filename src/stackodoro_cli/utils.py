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

    return "".join(result).rstrip()

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
