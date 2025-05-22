import sys
import os
import re

def parse_strings(lines):
    strings = {}
    collecting = False
    current_id = None
    current_content = []

    for line in lines:
        line_strip = line.strip()
        # Start of a string block
        if not collecting and line_strip.startswith('<string id="'):
            match = re.match(r'<string id="([^"]+)">', line_strip)
            if match:
                current_id = match.group(1)
                # Check if the closing tag is on the same line
                content_start = line_strip.find('>') + 1
                content_end = line_strip.find('</string>')
                if content_end != -1:
                    # Entire string in one line
                    content = line_strip[content_start:content_end]
                    strings[current_id] = content
                    current_id = None
                else:
                    # Start collecting multiline content
                    collecting = True
                    current_content = [line_strip[content_start:]]
        elif collecting:
            # Check if closing tag is found on this line
            if '</string>' in line_strip:
                content_end = line_strip.find('</string>')
                current_content.append(line_strip[:content_end])
                full_content = '\n'.join(current_content)
                strings[current_id] = full_content
                collecting = False
                current_id = None
                current_content = []
            else:
                current_content.append(line.rstrip('\n'))
    return strings

def parse_auto_static_blocks(lines, strings):
    collected = []
    buffer = []
    collecting_block = False
    attrs = {}
    key = None

    # Regex to parse attributes in the auto_static start tag
    attr_re = re.compile(r'(\w+)="([^"]*)"')

    def flush_block():
        nonlocal attrs, key
        if attrs and key is not None:
            # Convert numeric fields for sorting
            try:
                start_time = int(attrs.get('start_time', '0'))
            except:
                start_time = 0
            try:
                y = int(attrs.get('y', '0'))
            except:
                y = 0
            try:
                x = int(attrs.get('x', '0'))
            except:
                x = 0
            # Use strings dict to get text value for key, strip XML if any
            text_value = strings.get(key, '')
            # Remove any XML tags inside text_value just in case
            text_value = re.sub(r'<[^>]+>', '', text_value).strip()
            collected.append((start_time, y, x, text_value))
        attrs.clear()

    for line in lines:
        line_strip = line.strip()

        # Detect frame delimiter, output collected block sorted and deduplicated
        if line_strip == '<!-- next frame -->':
            if collected:
                # Sort by start_time, then y, then x
                collected.sort(key=lambda t: (t[0], t[1], t[2]))
                # Deduplicate consecutive identical lines
                output_lines = []
                last_line = None
                previous_x = 0 # add newline after carriage return
                for _, _, x, text in collected:
                    if text != last_line:
                        if previous_x < x:
                            output_lines.append('\n' + text)
                        else:
                            output_lines.append(text)
                        previous_x = x
                        last_line = text
                print('\n'.join(output_lines) + '\n')
            collected.clear()
            continue

        # Look for auto_static start tag, which can start with < or -<
        if (line_strip.startswith('<auto_static') or line_strip.startswith('-<auto_static')):
            # Extract attributes
            attrs = dict(attr_re.findall(line_strip))
            collecting_block = True
            key = None
            continue

        if collecting_block:
            # Look for <text ...>key</text> line
            # Can start with <text or -<text
            text_match = re.search(r'<?-?text[^>]*>(.*?)</text>', line_strip)
            if text_match:
                key = text_match.group(1).strip()
                # This should be the end of the block usually, but we wait for next block or frame
                flush_block()
                collecting_block = False

    # Flush at the end if any
    if collected:
        collected.sort(key=lambda t: (t[0], t[1], t[2]))
        output_lines = []
        last_line = None
        previous_x = 0 # add newline after carriage return
        for _, _, x, text in collected:
            if text != last_line:
                if previous_x > x:
                    output_lines.append('\n' + text)
                else:
                    output_lines.append(text)
                previous_x = x
                last_line = text
        print('\n'.join(output_lines) + '\n')

def main(input_path):
    output_path = os.path.splitext(input_path)[0] + '_credits.txt'

    with open(input_path, encoding='utf-8') as f:
        lines = f.readlines()

    strings = parse_strings(lines)

    collected = []
    output_frames = []
    frame_texts = []

    # We'll collect all auto_static blocks and output frames manually
    # so let's replicate parse_auto_static_blocks but write output to file instead of print

    attr_re = re.compile(r'(\w+)="([^"]*)"')

    collected = []
    collecting_block = False
    attrs = {}
    key = None

    def flush_block():
        nonlocal attrs, key
        if attrs and key is not None:
            try:
                start_time = int(attrs.get('start_time', '0'))
            except:
                start_time = 0
            try:
                y = int(attrs.get('y', '0'))
            except:
                y = 0
            try:
                x = int(attrs.get('x', '0'))
            except:
                x = 0
            text_value = strings.get(key, key)
            text_value = re.sub(r'<[^>]+>', '', text_value).strip()
            collected.append((start_time, y, x, text_value))
        attrs.clear()

    with open(output_path, 'w', encoding='utf-8') as fout:
        for line in lines:
            line_strip = line.strip()

            if line_strip == '<!-- next frame -->':
                if collected:
                    collected.sort(key=lambda t: (t[0], t[1], t[2]))
                    output_lines = []
                    last_line = None
                    previous_x = 0 # add newline after carriage return
                    for _, _, x, text in collected:
                        if text != last_line:
                            if previous_x < x:
                                output_lines.append('\n' + text)
                            else:
                                output_lines.append(text)
                            previous_x = x
                            last_line = text
                    fout.write('\n'.join(output_lines) + '\n\n')
                collected.clear()
                continue

            if line_strip.startswith('<auto_static') or line_strip.startswith('-<auto_static'):
                attrs = dict(attr_re.findall(line_strip))
                collecting_block = True
                key = None
                continue

            if collecting_block:
                text_match = re.search(r'<?-?text[^>]*>(.*?)</text>', line_strip)
                if text_match:
                    key = text_match.group(1).strip()
                    flush_block()
                    collecting_block = False

    print(f"Output written to: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <utf8_input_file>")
        sys.exit(1)
    main(sys.argv[1])
