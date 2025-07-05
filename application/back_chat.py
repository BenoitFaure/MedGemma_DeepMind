# Dependencies
import re
from back_get_rag_metadata import get_reference_dict


CITATION_DICT = get_reference_dict()

# Replace source by citation ID in the text, and add citation ID and title at the end
def cite_json_like(text: str) -> str:
    """
    Replaces every *.json or *.jsonl token in `text` with a numbered
    citation ([1], [2], …).  At the end of the text it appends a
    reference list, using `titles` to look‑up a human‑readable label.

    Parameters
    ----------
    text   : the input string.
    titles : dict mapping the exact file name (e.g.
             "10.2169_internalmedicine.5198-24.jsonl") -> title to show.

    Returns
    -------
    str – the annotated text.
    """
    # match words that end in .json or .jsonl, allowing dots, dashes, or underscores
    pattern = r'\b[A-Za-z0-9_.\-]+\.jsonl?\b'

    seen: dict[str, int] = {}      # filename -> citation number
    counter = 1                    # next citation number

    def repl(match: re.Match) -> str:
        nonlocal counter
        fname = match.group(0)
        if fname not in seen:      # first time we see this file
            seen[fname] = counter
            counter += 1
        return f'[{seen[fname]}]'

    # 1) replace occurrences with [n]
    body = re.sub(pattern, repl, text)

    # 2) build reference block
    refs = [
        f'[{n}] {CITATION_DICT.get(fname, "Unknown title")}'
        for fname, n in sorted(seen.items(), key=lambda x: x[1])
    ]

    return body + '\n\n' + '\n'.join(refs)



# Extract chunk ID from citation text
def extract_chunk_id(chunk):
    """
    Extract the chunk ID from citation text.
    
    Expected format: "chunk_id <id_value>\nchunk_text <text_content>"
    
    Args:
        chunk (str): The chunk text containing chunk_id
        
    Returns:
        str: The chunk ID, or None if not found
    """
    if not chunk:
        return None
    
    try:
        # Split by newline and get first line
        lines = chunk.split('\n')
        first_line = lines[0].strip()
        
        # Check if line starts with 'chunk_id '
        if first_line.startswith('chunk_id '):
            # Extract ID by removing the prefix
            chunk_id = first_line.replace('chunk_id ', '').strip()
            return chunk_id
            
        return None
        
    except Exception:
        return None