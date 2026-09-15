"""Patch fidelity meter core functionality."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Hunk:
    """Represents a single hunk in a diff."""
    
    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str]
    
    def get_changed_lines(self) -> list[str]:
        """Return lines that represent actual changes (+ or -)."""
        return [line for line in self.lines if line.startswith(('+', '-')) and not line.startswith(('+++', '---'))]
    
    def overlaps_with(self, other: 'Hunk') -> bool:
        """Check if this hunk overlaps with another hunk in the same file.
        
        Overlap is defined as: same file AND overlapping line ranges.
        We check both old and new line ranges for overlap.
        """
        if self.file_path != other.file_path:
            return False
        
        def ranges_overlap(start1: int, count1: int, start2: int, count2: int) -> bool:
            """Check if two ranges [start1, start1+count1) and [start2, start2+count2) overlap."""
            if count1 == 0 or count2 == 0:
                return False
            end1 = start1 + count1
            end2 = start2 + count2
            return start1 < end2 and start2 < end1
        
        old_overlap = ranges_overlap(self.old_start, self.old_count, other.old_start, other.old_count)
        new_overlap = ranges_overlap(self.new_start, self.new_count, other.new_start, other.new_count)
        
        return old_overlap or new_overlap


@dataclass
class Patch:
    """Represents a complete patch with multiple hunks."""
    
    hunks: list[Hunk]
    
    def get_files(self) -> set[str]:
        """Return set of all files touched by this patch."""
        return {hunk.file_path for hunk in self.hunks}
    
    def get_changed_lines(self) -> list[str]:
        """Return all changed lines across all hunks."""
        lines = []
        for hunk in self.hunks:
            lines.extend(hunk.get_changed_lines())
        return lines


def parse_unified_diff(diff_text: str) -> Patch:
    """Parse a unified diff into a Patch object.
    
    Supports standard unified diff format (diff -u) and git diff format.
    """
    hunks = []
    current_file: Optional[str] = None
    current_hunk_lines: list[str] = []
    current_old_start = 0
    current_old_count = 0
    current_new_start = 0
    current_new_count = 0
    
    lines = diff_text.strip().split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('--- '):
            if current_file is not None and current_hunk_lines:
                hunks.append(Hunk(
                    file_path=current_file,
                    old_start=current_old_start,
                    old_count=current_old_count,
                    new_start=current_new_start,
                    new_count=current_new_count,
                    lines=current_hunk_lines
                ))
                current_hunk_lines = []
            
            old_file = line[4:].strip()
            if old_file.startswith('a/'):
                old_file = old_file[2:]
            
            if i + 1 < len(lines) and lines[i + 1].startswith('+++ '):
                new_file = lines[i + 1][4:].strip()
                if new_file.startswith('b/'):
                    new_file = new_file[2:]
                current_file = new_file if new_file != '/dev/null' else old_file
                i += 1
            else:
                current_file = old_file
        
        elif line.startswith('@@'):
            if current_file is not None and current_hunk_lines:
                hunks.append(Hunk(
                    file_path=current_file,
                    old_start=current_old_start,
                    old_count=current_old_count,
                    new_start=current_new_start,
                    new_count=current_new_count,
                    lines=current_hunk_lines
                ))
                current_hunk_lines = []
            
            parts = line.split('@@')
            if len(parts) >= 2:
                ranges = parts[1].strip().split()
                if len(ranges) >= 2:
                    old_range = ranges[0][1:]
                    new_range = ranges[1][1:]
                    
                    if ',' in old_range:
                        old_start_str, old_count_str = old_range.split(',')
                        current_old_start = int(old_start_str)
                        current_old_count = int(old_count_str)
                    else:
                        current_old_start = int(old_range)
                        current_old_count = 1
                    
                    if ',' in new_range:
                        new_start_str, new_count_str = new_range.split(',')
                        current_new_start = int(new_start_str)
                        current_new_count = int(new_count_str)
                    else:
                        current_new_start = int(new_range)
                        current_new_count = 1
        
        elif current_file is not None and (line.startswith(('+', '-', ' ')) or line == ''):
            current_hunk_lines.append(line)
        
        i += 1
    
    if current_file is not None and current_hunk_lines:
        hunks.append(Hunk(
            file_path=current_file,
            old_start=current_old_start,
            old_count=current_old_count,
            new_start=current_new_start,
            new_count=current_new_count,
            lines=current_hunk_lines
        ))
    
    return Patch(hunks=hunks)
