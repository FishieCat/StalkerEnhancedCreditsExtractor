import sys
import os

def process_file(input_path):
    output_path = os.path.splitext(input_path)[0] + '_strip.xml'
    skipped_lines = 0

    with open(input_path, 'rb') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
        for line_num, byte_line in enumerate(f_in, 1):
            try:
                decoded_line = byte_line.decode('windows-1250')
            except UnicodeDecodeError:
                # Skip the line with a newline, count as skipped
                f_out.write('\n')
                skipped_lines += 1
                continue
            
            stripped_line = decoded_line.strip()
            if stripped_line.startswith('-'): # for some reason some lines start with -
                stripped_line = stripped_line[1:]
            if stripped_line.startswith('<') and stripped_line.endswith('>'):
                f_out.write(stripped_line + '\n')

    print(f"Processing complete. Skipped {skipped_lines} unreadable line(s). Output saved to: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file>")
        sys.exit(1)

    process_file(sys.argv[1])
