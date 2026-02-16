from .models import AsciiArtAsset

def merge_assets(base: AsciiArtAsset, overlay: AsciiArtAsset, start_y: int) -> None:
    required_height = start_y + len(overlay.lines)
    
    if required_height > len(base.lines):
        extension_len = required_height - len(base.lines)
        base.lines.extend([""] * extension_len)
        base.colors.extend([[] for _ in range(extension_len)])

    for i, fg_line in enumerate(overlay.lines):
        current_y = start_y + i
        if current_y < 0: 
            continue
            
        bg_line = base.lines[current_y]
        fg_colors = overlay.colors[i] if i < len(overlay.colors) else []
        bg_colors = base.colors[current_y]
        
        stripped_fg = fg_line.strip()
        max_len = max(len(bg_line), len(fg_line))
        
        def pad_colors(color_list, length):
            color_list.extend([None] * max(0, length - len(color_list)))

        if not stripped_fg:
            base.lines[current_y] = bg_line.ljust(max_len)
            pad_colors(bg_colors, max_len)
            continue

        # solid bounds of the foreground art
        start_index = fg_line.find(stripped_fg[0])
        end_index = fg_line.rfind(stripped_fg[-1])
        
        bg_line = bg_line.ljust(max_len)
        pad_colors(bg_colors, max_len)
        
        fg_colors_padded = list(fg_colors)
        pad_colors(fg_colors_padded, max_len)
        
        merged_line = list(bg_line)
        for x in range(start_index, end_index + 1):
            merged_line[x] = fg_line[x]
            if fg_colors_padded[x] is not None:
                bg_colors[x] = fg_colors_padded[x]
                
        base.lines[current_y] = "".join(merged_line)

def render_urwid_markup(asset: AsciiArtAsset) -> list:
    markup = []
    
    for y, line in enumerate(asset.lines):
        if y >= len(asset.colors):
            markup.append(line)
            markup.append('\n')
            continue
            
        row_attrs = asset.colors[y]
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

def format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"
    