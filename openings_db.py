import os
import re

OPENINGS = []
 
def load_openings():
    global OPENINGS
    OPENINGS = []
     
    if not os.path.exists('Openings.txt'):
        print("Openings.txt file not found. Using minimal opening database.")
        OPENINGS = [
            ("e4 e5 Nf3 Nc6 Bc4", "Italian Game", "1.e4 e5 2.Nf3 Nc6 3.Bc4"),
            ("e4 e5 Nf3 Nc6 Bc4 Bc5", "Italian Game, Giuoco Piano", "1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5"),
            ("e4 e5 Nf3 Nc6 Bb5", "Ruy Lopez", "1.e4 e5 2.Nf3 Nc6 3.Bb5"),
            ("e4 c5", "Sicilian Defense", "1.e4 c5"),
            ("e4 e6", "French Defense", "1.e4 e6"),
            ("e4 c6", "Caro-Kann Defense", "1.e4 c6"),
            ("d4 d5 c4", "Queen's Gambit", "1.d4 d5 2.c4"),
            ("c4", "English Opening", "1.c4"),
            ("Nf3", "Reti Opening", "1.Nf3"),
            ("g3", "King's Fianchetto Opening", "1.g3")
        ]
        return
     
    try:
        content = None
        for encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
            try:
                with open('Openings.txt', 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise Exception("Could not read Openings.txt with any encoding")
             
        lines = content.split('\n')
        total_lines = len(lines)
        processed_lines = 0
        matched_lines = 0
        chess_lines = 0
         
        for line in lines:
            line = line.strip()
            if not line:
                continue
             
            processed_lines += 1
             
            if line.startswith(('A ', 'B ', 'C ', 'D ', 'E ')) or '  ' in line:
                continue
             
            if ':' not in line:
                continue
                
            if any(move in line for move in ['1.', 'e4', 'd4', 'c4', 'Nf3', 'g3', 'b3', 'e3', 'a3', 'h3']):
                chess_lines += 1
            pattern1 = r'^([1-9][\w\s\d\-\+\=\.]+?):\s*(.+?)\s*\(([^)]+)\)$'
            pattern2 = r'^([1-9][\w\s\d\-\+\=\.]+?):\s*(.+)$'
            pattern3 = r'^(.+?):\s*([1-9][\w\s\d\-\+\=\.]+?)\s*\(([^)]+)\)$'
            pattern4 = r'^(.+?):\s*([1-9][\w\s\d\-\+\=\.]+?)$'
            
            match1 = re.match(pattern1, line)
            match2 = re.match(pattern2, line)
            match3 = re.match(pattern3, line)
            match4 = re.match(pattern4, line)
            
            move_line = None
            opening_name = None
            
            if match1:
                move_line = match1.group(1).strip()
                opening_name = match1.group(2).strip()
            elif match2:
                move_line = match2.group(1).strip()
                opening_name = match2.group(2).strip()
            elif match3:
                opening_name = match3.group(1).strip()
                move_line = match3.group(2).strip()
            elif match4:
                opening_name = match4.group(1).strip()
                move_line = match4.group(2).strip()
            
            if move_line and opening_name:
                clean_moves = re.sub(r'\d+\.', '', move_line).strip()
                clean_moves = re.sub(r'\s+', ' ', clean_moves).strip()
                if clean_moves and opening_name:
                    OPENINGS.append((clean_moves, opening_name, move_line))
                    matched_lines += 1
        
        print(f"Processed {processed_lines} lines out of {total_lines} total lines")
        print(f"Found {chess_lines} lines with chess notation")
        print(f"Matched {matched_lines} opening entries")
    except Exception as e:
        print(f"Error loading openings from file: {e}")
        OPENINGS = [
            ("e4 e5 Nf3 Nc6 Bc4", "Italian Game", "1.e4 e5 2.Nf3 Nc6 3.Bc4"),
            ("e4 e5 Nf3 Nc6 Bc4 Bc5", "Italian Game, Giuoco Piano", "1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5"),
            ("e4 e5 Nf3 Nc6 Bb5", "Ruy Lopez", "1.e4 e5 2.Nf3 Nc6 3.Bb5"),
            ("e4 c5", "Sicilian Defense", "1.e4 c5"),
            ("e4 e6", "French Defense", "1.e4 e6"),
            ("e4 c6", "Caro-Kann Defense", "1.e4 c6"),
            ("d4 d5 c4", "Queen's Gambit", "1.d4 d5 2.c4"),
            ("c4", "English Opening", "1.c4"),
            ("Nf3", "Reti Opening", "1.Nf3"),
            ("g3", "King's Fianchetto Opening", "1.g3")
        ]
 
def get_opening_info(move_stack):
    if not move_stack:
        return ("Starting Position", "")
         
    moves_str = " ".join(move_stack)
    best_match_name = "Unknown Opening"
    best_match_line = ""
    best_match_length = 0
     
    for opening_moves, opening_name, move_line in OPENINGS:
        if moves_str.startswith(opening_moves):
            if len(opening_moves) > best_match_length:
                best_match_name = opening_name
                best_match_line = move_line
                best_match_length = len(opening_moves)
     
    return (best_match_name, best_match_line)

load_openings()